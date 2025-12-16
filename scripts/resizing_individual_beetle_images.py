#!/usr/bin/env python3

import csv
import json
import os
from PIL import Image
import numpy as np

# Set Base Directories
BASE_DIR = "2018-NEON-beetles"
ORIGINAL_GROUP_IMAGES_DIR = os.path.join(BASE_DIR, "group_images")
PROCESS_DIR = os.path.join(BASE_DIR, "processed_images")

def calculate_uniform_scaling_factors():
    """
    Calculate uniform scaling factors between original group images and BeetlePalooza resized images.
    Returns a dictionary mapping picture_id -> uniform_scale_factor
    """
    scaling_factors = {}
    
    print("Step 1: Calculating uniform scaling factors between original and resized group images...")
    
    # Get list of resized images
    if not os.path.exists(PROCESS_DIR):
        print(f"Error: Directory {PROCESS_DIR} does not exist")
        return {}
    
    resized_files = [f for f in os.listdir(PROCESS_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"Found {len(resized_files)} resized images")
    
    processed = 0
    for resized_filename in resized_files:
        # Extract picture_id (remove extension)
        picture_id = os.path.splitext(resized_filename)[0]
        
        # Find corresponding original image
        original_path = None
        for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
            potential_path = os.path.join(ORIGINAL_GROUP_IMAGES_DIR, picture_id + ext)
            if os.path.exists(potential_path):
                original_path = potential_path
                break
        
        if original_path is None:
            print(f"Warning: No original image found for {picture_id}")
            continue
        
        # Load both images and get dimensions
        resized_path = os.path.join(PROCESS_DIR, resized_filename)

        try:
            with Image.open(original_path) as orig_img:
                orig_width, orig_height = orig_img.size
            
            with Image.open(resized_path) as resized_img:
                resized_width, resized_height = resized_img.size
            
            # Calculate scaling factors (original / resized)
            scale_x = orig_width / resized_width
            scale_y = orig_height / resized_height
            
            # Use uniform scaling factor (average of x and y)
            uniform_scale = (scale_x + scale_y) / 2
            
            scaling_factors[picture_id] = uniform_scale
            processed += 1
            
            if processed % 100 == 0:
                print(f"  Processed {processed} images...")
                
        except Exception as e:
            print(f"Error processing {picture_id}: {e}")
    
    print(f"Calculated uniform scaling factors for {len(scaling_factors)} images")
    
    # Calculate statistics
    if scaling_factors:
        scale_values = list(scaling_factors.values())
        print(f"Scaling factor statistics:")
        print(f"  Min: {min(scale_values):.3f}")
        print(f"  Max: {max(scale_values):.3f}")
        print(f"  Mean: {np.mean(scale_values):.3f}")
        print(f"  Std: {np.std(scale_values):.3f}")
    
    # Save scaling factors to JSON file for reference
    output_json = os.path.join(PROCESS_DIR, "uniform_scaling_factors.json")
    with open(output_json, 'w') as f:
        json.dump(scaling_factors, f, indent=2, sort_keys=True)
    print(f"Uniform scaling factors saved to: {output_json}")
    
    return scaling_factors

def resize_image_uniform(input_path, output_path, scale_factor):
    """
    Resize an individual image using a uniform scaling factor.
    
    Args:
        input_path: Path to input image
        output_path: Path to save resized image
        scale_factor: Uniform scaling factor (original_size / resized_size)
    """
    with Image.open(input_path) as img:
        original_width, original_height = img.size
        
        # Calculate new dimensions using uniform scaling
        new_width = int(original_width / scale_factor)
        new_height = int(original_height / scale_factor)
        
        # Resize using high-quality resampling
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save the resized image
        resized_img.save(output_path, optimize=True)

def resize_individual_images_uniform():
    """
    Resize all individual specimen images using uniform scaling factors.
    """
    # Calculate uniform scaling factors first
    scaling_factors = calculate_uniform_scaling_factors()
    
    if not scaling_factors:
        print("Error: No scaling factors calculated. Exiting.")
        return
    
    # Show some example scaling factors
    print("\nExample uniform scaling factors for first 5 group images:")
    for i, (picture_id, scale) in enumerate(list(scaling_factors.items())[:5]):
        print(f"  {picture_id}: uniform_scale={scale:.3f}")
    
    print("\nStep 2: Resizing individual specimen images using uniform scaling...")
    
    # Paths
    csv_file = os.path.join(BASE_DIR, "individual_specimens.csv")
    output_dir = os.path.join(PROCESS_DIR, "individual_images_resized_uniform")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read CSV file
    individual_images = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            individual_images.append(row)
    
    print(f"Found {len(individual_images)} individual images to process")
    
    processed = 0
    skipped = 0
    errors = 0
    
    for row in individual_images:
        try:
            # Get the image paths
            individual_path_rel = row['individualImageFilePath']
            group_image_filename = os.path.basename(row['groupImageFilePath'])
            picture_id = os.path.splitext(group_image_filename)[0]
            
            # Check if we have scaling factors for this group image
            if picture_id not in scaling_factors:
                skipped += 1
                continue
            
            # Full path to individual image
            individual_path_full = os.path.join(BASE_DIR, individual_path_rel)
            
            if not os.path.exists(individual_path_full):
                skipped += 1
                continue
            
            # Output path (maintain directory structure)
            output_path = os.path.join(output_dir, individual_path_rel)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Get uniform scaling factor
            scale_factor = scaling_factors[picture_id]
            
            # Resize the image using uniform scaling
            resize_image_uniform(individual_path_full, output_path, scale_factor)
            
            processed += 1
            if processed % 100 == 0:
                print(f"  Processed {processed} images...")
                
        except Exception as e:
            print(f"Error processing {individual_path_rel}: {str(e)}")
            errors += 1
    
    print(f"\nProcessing complete!")
    print(f"  Successfully processed: {processed}")
    print(f"  Skipped (no scaling factor): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Output directory: {output_dir}")
    
    # Save processing summary
    summary = {
        "total_individual_images": len(individual_images),
        "successfully_processed": processed,
        "skipped_no_scaling_factor": skipped,
        "errors": errors,
        "scaling_factors_used": len(scaling_factors),
        "output_directory": output_dir,
        "scaling_method": "uniform"
    }
    
    summary_path = os.path.join(output_dir, "processing_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Processing summary saved to: {summary_path}")

if __name__ == "__main__":
    print("=== Improved Individual Image Resizing Script (Uniform Scaling) ===")
    print("This script uses uniform scaling factors for simpler and more consistent")
    print("image resizing while maintaining aspect ratios.")
    print()
    
    resize_individual_images_uniform()
