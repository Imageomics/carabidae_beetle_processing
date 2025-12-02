import warnings
import os
import csv
import json
import uuid
import torch
import transformers
import pandas as pd
import torchvision.ops as ops
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
import argparse


def point_inside_box(point, box):
    px, py = point
    bx1, by1, bx2, by2 = box
    return bx1 <= px <= bx2 and by1 <= py <= by2   # Check if a point lies within a bounding box


def detect(image, processor, model, text, box_threshold, text_threshold, device):
    # Prepare model inputs (image + text prompt)
    inputs = processor(images=image, text=text, return_tensors="pt").to(device)

    with torch.no_grad():   # Disable gradient computation for inference
        outputs = model(**inputs)

    # Convert model outputs into actual bounding boxes
    results = processor.post_process_grounded_object_detection(
        outputs, inputs.input_ids,
        box_threshold=box_threshold,
        text_threshold=text_threshold,
        target_sizes=[image.size[::-1]]
    )
    return results


def process_single_image(image_path, df, save_folder, text, box_threshold, text_threshold,
                         padding, iou_threshold, device, processor, model):

    image = Image.open(image_path).convert("RGB")   # Load image
    img_width, img_height = image.size
    img_area = img_width * img_height

    base_name = os.path.basename(image_path)
    image_dir = os.path.join(save_folder, base_name)
    os.makedirs(image_dir, exist_ok=True)           # Make directory for that group image

    beetles = df[df['pictureID'] == base_name]      # All beetle entries for this image
    if beetles.empty:
        return False

    csv_path = os.path.join(image_dir, f"{os.path.splitext(base_name)[0]}.csv")

    # Run Grounding-DINO detection
    results = detect(image, processor, model, text, box_threshold, text_threshold, device)

    detected_any = False

    with open(csv_path, mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        # Write header only once
        if os.stat(csv_path).st_size == 0:
            csv_writer.writerow(["pictureID", "beetle_uuid", "x_min", "y_min", "x_max", "y_max", "score"])

        # Process each beetle in that image
        for beetle_uuid, beetle_data in beetles.groupby('beetle_uuid'):

            # Extract elytra length/width coordinate dictionaries
            elytra_length = beetle_data['length_coord_value'].dropna().values
            elytra_width = beetle_data['width_coord_value'].dropna().values

            elytra_length = eval(elytra_length[0]) if len(elytra_length) > 0 else None
            elytra_width = eval(elytra_width[0]) if len(elytra_width) > 0 else None

            # Convert dicts to line endpoints
            elytra_length_line = [(elytra_length['x1'], elytra_length['y1']),
                                  (elytra_length['x2'], elytra_length['y2'])] if elytra_length else None
            elytra_width_line = [(elytra_width['x1'], elytra_width['y1']),
                                 (elytra_width['x2'], elytra_width['y2'])] if elytra_width else None

            best_box = None
            max_area = 0
            best_score = 0
            all_boxes = []
            all_scores = []

            # Iterate through all detected boxes
            for result in results:
                num_detections = len(result["boxes"])

                for box, score in zip(result["boxes"], result["scores"]):
                    box = [int(coord) for coord in box]
                    bbox_area = (box[2] - box[0]) * (box[3] - box[1])

                    # Dismiss boxes too large relative to image, based on count (dynamic thresholding)
                    if 5 < num_detections and bbox_area > 0.1 * img_area: continue
                    if 5 <= num_detections < 20 and bbox_area > 0.05 * img_area: continue
                    if 20 <= num_detections < 50 and bbox_area > 0.02 * img_area: continue
                    if 50 <= num_detections < 100 and bbox_area > 0.01 * img_area: continue
                    if 100 <= num_detections < 200 and bbox_area > 0.005 * img_area: continue
                    if 200 <= num_detections and bbox_area > 0.001 * img_area: continue

                    # Check: the box must fully contain the elytra measurement lines
                    if elytra_length_line and elytra_width_line and \
                       point_inside_box(elytra_length_line[0], box) and point_inside_box(elytra_length_line[1], box) and \
                       point_inside_box(elytra_width_line[0], box) and point_inside_box(elytra_width_line[1], box):

                        all_boxes.append(torch.tensor(box).float())
                        all_scores.append(score)

            # Apply NMS to remove overlapping detections
            if len(all_boxes) > 0:
                all_boxes = torch.stack(all_boxes)
                all_scores = torch.tensor(all_scores)
                keep = ops.nms(all_boxes, all_scores, iou_threshold)

                # Select largest retained box
                for idx in keep:
                    box = all_boxes[idx].int().tolist()
                    score = all_scores[idx].item()
                    bbox_area = (box[2] - box[0]) * (box[3] - box[1])
                    if bbox_area > max_area:
                        max_area = bbox_area
                        best_box = box
                        best_score = score

            # Save crop if we found a valid box
            if best_box:
                detected_any = True
                detection_filename = f"{beetle_uuid}.png"
                detection_path = os.path.join(image_dir, detection_filename)

                # Add padding around detection box
                padding_w = int(padding * (best_box[2] - best_box[0]))
                padding_h = int(padding * (best_box[3] - best_box[1]))
                x_min = max(0, best_box[0] - padding_w)
                y_min = max(0, best_box[1] - padding_h)
                x_max = min(img_width, best_box[2] + padding_w)
                y_max = min(img_height, best_box[3] + padding_h)

                cropped_image = image.crop((x_min, y_min, x_max, y_max))

                # Resize crop to fit inside 512×512 (preserving aspect ratio)
                crop_width, crop_height = cropped_image.size
                scale = 512 / max(crop_width, crop_height)
                new_width, new_height = int(crop_width * scale), int(crop_height * scale)

                resized_image = cropped_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Center-pad with ImageNet RGB mean
                padded_image = Image.new("RGB", (512, 512), (123, 116, 103))
                paste_x = (512 - new_width) // 2
                paste_y = (512 - new_height) // 2
                padded_image.paste(resized_image, (paste_x, paste_y))
                padded_image.save(detection_path, "PNG")

                # Write detection row
                csv_writer.writerow([base_name, beetle_uuid, *best_box, round(float(best_score), 4)])

                # Update row in master DataFrame
                df.loc[
                    (df["pictureID"] == base_name) & (df["beetle_uuid"] == beetle_uuid),
                    "individual_image_file_path"
                ] = os.path.join("individual_images", base_name, detection_filename)

    return detected_any


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process beetle images using Grounding-DINO.")
    parser.add_argument("--csv_path", required=True, help="Path to the input CSV file.")
    parser.add_argument("--image_dir", required=True, help="Directory containing group images.")
    parser.add_argument("--save_folder", required=True, help="Folder to save individual images and CSVs.")
    parser.add_argument("--output_csv", required=True, help="Path to save the output CSV file.")
    parser.add_argument("--model_id", default="IDEA-Research/grounding-dino-base", help="Model ID for Grounding-DINO.")
    parser.add_argument("--text", default="a beetle.", help="Text prompt for detection.")
    parser.add_argument("--box_threshold", type=float, default=0.2, help="Box threshold for detection.")
    parser.add_argument("--text_threshold", type=float, default=0.2, help="Text threshold for detection.")
    parser.add_argument("--padding", type=float, default=0.1, help="Padding factor for cropping.")
    parser.add_argument("--iou_threshold", type=float, default=0.6, help="IoU threshold for NMS.")
    
    args = parser.parse_args()

    warnings.filterwarnings("ignore")

    df = pd.read_csv(args.csv_path)

    # Compute resized image filepath (used elsewhere in your workflow)
    df["resized_image_filepath"] = df["raw_filepath"].str.replace("group_images", "resized_images", regex=False)

    # Choose preferred annotator; fallback to first annotator
    selected_rows = []
    for (beetleID, pictureID), group in df.groupby(['beetleID', 'pictureID']):
        if 'specific_user' in group['user_name'].values:
            selected_row = group[group['user_name'] == 'specific_user'].iloc[0]
        else:
            selected_row = group.iloc[0]
        selected_rows.append(selected_row)
    df = pd.DataFrame(selected_rows)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load Grounding-DINO
    processor = AutoProcessor.from_pretrained(args.model_id)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(args.model_id).to(device)

    # Prepare list of image paths to process
    image_files = df["pictureID"].unique().tolist()
    image_path_list = [os.path.join(args.image_dir, file) for file in image_files]

    # Ensure output column exists
    for col in ["individual_image_file_path"]:
        if col not in df.columns:
            df[col] = None

    os.makedirs(args.save_folder, exist_ok=True)

    detected_images = set()

    # Process each group image
    for image_path in image_path_list:
        if process_single_image(image_path, df, args.save_folder, args.text,
                                args.box_threshold, args.text_threshold, args.padding,
                                args.iou_threshold, device, processor, model):
            detected_images.add(os.path.basename(image_path))

    # Save updated metadata CSV
    df.to_csv(args.output_csv, index=False)
