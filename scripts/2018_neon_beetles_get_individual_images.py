#!/usr/bin/env python3

import os
import argparse
import xml.etree.ElementTree as ET
from PIL import Image
from tqdm import tqdm

def parse_cvat_annotations(xml_path):
    """Parse the CVAT XML file and extract image names and bounding boxes."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    images_data = []
    
    # Iterate through all image elements in the XML
    for image_elem in root.findall('.//image'):
        # Get the full image name from XML
        full_image_name = image_elem.get('name')
        # Extract just the filename part (remove any directory components)
        image_name = os.path.basename(full_image_name)
        image_width = int(image_elem.get('width'))
        image_height = int(image_elem.get('height'))
        
        boxes = []
        # Get all bounding boxes for this image
        for box_elem in image_elem.findall('.//box'):
            x_min = float(box_elem.get('xtl'))
            y_min = float(box_elem.get('ytl'))
            x_max = float(box_elem.get('xbr'))
            y_max = float(box_elem.get('ybr'))
            
            boxes.append((x_min, y_min, x_max, y_max))

        images_data.append({
            'filename': image_name,
            'width': image_width,
            'height': image_height,
            'boxes': boxes
        })
    
    return images_data

def crop_and_save_images(images_data, images_dir, output_dir, padding=0):
    """Crop images based on bounding boxes and save them."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    total_crops = sum(len(img['boxes']) for img in images_data)
    print(f"Found {len(images_data)} images with {total_crops} total bounding boxes to crop")
    
    crop_count = 0
    for img_data in tqdm(images_data, desc="Processing images"):
        image_path = os.path.join(images_dir, img_data['filename'])
        
        # Skip if file doesn't exist
        if not os.path.exists(image_path):
            print(f"Warning: Image {img_data['filename']} not found in {images_dir}")
            continue
        
        # Open the image
        try:
            img = Image.open(image_path)
            
            # Process each bounding box
            for i, box in enumerate(img_data['boxes']):
                # Add padding if specified
                x_min = max(0, int(box[0]) - padding)
                y_min = max(0, int(box[1]) - padding)
                x_max = min(img_data['width'], int(box[2]) + padding)
                y_max = min(img_data['height'], int(box[3]) + padding)
                
                # Crop the image using bounding box coordinates
                cropped_img = img.crop((x_min, y_min, x_max, y_max))
                
                # Generate output filename
                base_name = os.path.splitext(img_data['filename'])[0]
                output_filename = f"{base_name}_specimen_{i+1}.png"
                output_path = os.path.join(output_dir, output_filename)

                # Save the cropped image
                cropped_img.save(output_path)
                crop_count += 1
                
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
    
    print(f"Successfully cropped and saved {crop_count} beetle images")

def main():
    parser = argparse.ArgumentParser(description="Extract and save cropped beetle images from CVAT annotations")
    parser.add_argument("--xml_file", required=True, help="Path to the CVAT XML annotation file")
    parser.add_argument("--images_dir", required=True, help="Directory containing the original images")
    parser.add_argument("--output_dir", required=True, help="Directory to save the cropped beetle images")
    parser.add_argument("--padding", type=int, default=0, help="Additional padding around each bounding box (default: 5 pixels)")
    
    args = parser.parse_args()
    
    # Parse the XML annotations
    print(f"Parsing annotations from {args.xml_file}...")
    images_data = parse_cvat_annotations(args.xml_file)
    
    # Crop and save images
    print(f"Cropping beetle images and saving to {args.output_dir}...")
    crop_and_save_images(images_data, args.images_dir, args.output_dir, args.padding)

if __name__ == "__main__":
    main()
