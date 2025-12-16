# Carabidae Beetle Processing Pipeline

**Automated Processing and Quality Assessment for Beetle Morphometric Data**

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Project Structure](#-project-structure)
- [Pipeline Components](#-pipeline-components)
  - [1. Image Annotation and Extraction](#1-image-annotation-and-extraction)
  - [2. Traditional Bouding Box Cropping (Individual Beetle Extraction)](#2-traditional-bounding-box-cropping)
  - [3. Image Resizing with Uniform Scaling](#3-image-resizing-with-uniform-scaling)
  - [4. Zero-Shot Object Detection](#4-zero-shot-object-detection)
  - [5. Quality Control and Validation](#5-quality-control-and-validation)
  - [6. NEON Data Analysis and Visualization](#6-neon-data-analysis-and-visualization)
  - [7. Dataset Upload to Hugging Face](#7-dataset-upload-to-hugging-face)
- [Installation](#%EF%B8%8F-installation)
- [Data Sources](#-data-sources)
- [Citation](#-citation)
- [Acknowledgements](#acknowledgments)

---

## 🎯 Overview

This repository contains the complete pipeline used for processing, analyzing, and validating beetle specimen images and morphometric measurements for the [2018 NEON Ethanol-preserved Ground Beetles](https://huggingface.co/datasets/imageomics/2018-NEON-beetles) and [Hawaii Beetles](https://huggingface.co/datasets/imageomics/Hawaii-beetles) datasets. The project focuses on **Carabidae** (ground beetles) and implements:

1. **Automated beetle detection and cropping** from group images using CVAT annotations and zero-shot object detection.
2. **Morphometric trait extraction** including elytra length and width measurements.
3. **Inter-annotator agreement analysis** comparing measurements between human annotators.
4. **Human vs. automated system validation** evaluating algorithmic measurements against manual measurements.
5. **Species distribution visualization** for PUUM (Pu'u Maka'ala Natural Area Reserve, Hawaii) site data.

The pipeline integrates computer vision (Grounding DINO), traditional image processing, and statistical validation to create a robust, reproducible workflow for entomological specimen digitization.

---

## 📁 Project Structure

```
carabidae_beetle_processing/
├── annotations/
|    └── 2018_neon_beetles_bbox.xml                 # CVAT annotations (577 images)
├── notebooks/
|    └── grounding_dino.ipynb                       # Zero-shot object detection pipeline
├── scripts/
|    ├── 2018_neon_beetles_get_individual_images.py # Crop beetles from group images
|    ├── Figure6and10.R                             # NEON data analysis and visualization
|    ├── beetle_detection.py                        # Grounding-Dino-based detection of beetles
|    ├── calipers_vs_toras.py                       # Human vs. automated measurement comparison
|    ├── inter_annotator.py                         # Inter-annotator agreement analysis
|    ├── resizing_individual_beetle_images.py       # Resize individual images with uniform scaling
|    └── upload_dataset_to_hf.py                    # Upload datasets to Hugging Face
├── .gitignore                                      # Git ignore patterns
├── CITATION.cff                                    # Citation metadata
├── LICENSE                                         # MIT License
├── requirements.txt                                # Python dependencies
└── README.md                                       # This file
```

---

## 🔬 Pipeline Components

The pipeline and usage instructions are provided below. Please be sure to set up your coding environments appropriately for the needed portion of the pipeline (see [Installation](#%EF%B8%8F-installation) for detailed guidance).

### 1. **Image Annotation and Extraction**

**File:** `2018_neon_beetles_bbox.xml`

CVAT (Computer Vision Annotation Tool) annotations containing:
- 577 annotated images
- Bounding box coordinates for individual beetles in group images
- Image dimensions (5568 × 3712 pixels)

**Format:**
```xml
<image id="0" name="group_images/A00000001831.jpg" width="5568" height="3712">
    <box label="bbox" xtl="2051.88" ytl="1881.84" xbr="2417.17" ybr="2473.22"/>
    ...
</image>
```

### 2. **Traditional Bounding Box Cropping**

**Script:** `2018_neon_beetles_get_individual_images.py`

Extracts individual beetle specimens from group images using CVAT XML bounding box annotations. Parses coordinates, crops specimens with optional padding, and saves as numbered PNG files with progress tracking.

#### Usage Instructions

Extract individual beetles from group images using CVAT annotations:

```bash
python scripts/2018_neon_beetles_get_individual_images.py \
    --xml_file annotations/2018_neon_beetles_bbox.xml \
    --images_dir /path/to/group_images/ \
    --output_dir /path/to/individual_beetles/ \
    --padding 0
```

Outputs individual beetle images named `{original_name}_specimen_{N}.png`.

### 3. **Image Resizing with Uniform Scaling**

**Script:** `resizing_individual_beetle_images.py`

Aligns individual beetle crops with the 2018-NEON-Beetles Zooniverse-processed group images by applying uniform scaling factors. This enables accurate transfer of citizen science measurements from resized group images to individual specimens. Set proper base directories at the top of the script before use.

**Workflow:**
1. Calculate uniform scaling factors (average of x and y) between original and resized group images
2. Apply scaling to all individual specimen images
3. Save scaling metadata and processing statistics to JSON

### 4. **Zero-Shot Object Detection**

**Script:** `beetle_detection.py` | **Notebook:** `grounding_dino.ipynb`

Automated beetle detection pipeline using **Grounding DINO** zero-shot object detection. The script version provides a command-line interface for the notebook workflow.

**Basic Usage:**

```console
python scripts/beetle_detection.py \
  --csv_path data/metadata.csv \
  --image_dir data/group_images \
  --save_folder data/individual_images \
  --output_csv data/processed.csv
```

Optional parameters: `--model_id` (default: `IDEA-Research/grounding-dino-base`), `--text` (prompt, default: `"a beetle."`), `--box_threshold` (0.2), `--text_threshold` (0.2), `--padding` (0.1), `--iou_threshold` (0.6).

The pipeline detects beetles using text prompts, filters by adaptive area thresholds, validates measurement points, applies NMS to remove duplicates, and selects optimal bounding boxes before saving crops and metadata.

### 5. Quality Control and Validation

#### Inter-Annotator Agreement

**Script:** `inter_annotator.py`

Quantifies measurement consistency between human annotators using three pairwise comparisons. Computes RMSE (measurement disagreement), R² (correlation strength), and average bias (systematic tendencies). Generates `InterAnnotatorAgreement.pdf` with scatter plots and console metrics report.

```bash
python scripts/inter_annotator.py
```

Edit `DATA_PATH` and `ANNOTATOR_PAIRS` in the script to configure input data and comparisons. Outputs `InterAnnotatorAgreement.pdf` and console metrics.

#### Human vs. Automated System

**Script:** `calipers_vs_toras.py`

Validates automated TORAS measurements against human caliper measurements (gold standard). Compares three annotators individually and averaged against the automated system using RMSE, R², and bias metrics. Generates `CalipersVsToras.pdf` with comparison plots.

```bash
python scripts/calipers_vs_toras.py
```

Edit configuration variables in the script for data paths and comparison pairs. Generates `CalipersVsToras.pdf` with validation metrics.

### 6. **NEON Data Analysis and Visualization**

**Script:** `Figure6and10.R`

Analyzes NEON beetle data from PUUM site (Pu'u Maka'ala Natural Area Reserve, Hawaii) integrated with BeetlePalooza citizen science measurements. Retrieves data via NEON API, merges taxonomic identifications with morphometric measurements, and generates species abundance visualizations. Produces `BeetlePUUM_abundance.png` showing imaging status and merged analysis dataset.

Run R script for NEON data analysis:

```bash
Rscript scripts/Figure6and10.R
```

Requires NEON API token saved in `NEON_Token.txt` (see [NEON token instructions](#neon-api-token)) and BeetlePalooza metadata (2018-NEON-Beetles `individual_metadata.csv`). Edit paths in script as needed. Produces `BeetlePUUM_abundance.png` showing species distributions.

**Requirements:** R packages: `ggplot2`, `dplyr`, `ggpubr`, `neonUtilities`

### 7. **Dataset Upload to Hugging Face**

**Script:** `upload_dataset_to_hf.py`

Utility script used to upload the processed beetle datasets to Hugging Face Hub for public access and reproducibility.

**Usage:**
```bash
export HF_TOKEN="your_hugging_face_token"

python upload_dataset_to_hf.py \
    --folder_path /path/to/local/images \
    --repo_id imageomics/dataset-name \
    --path_in_repo images \
    --branch main
```

**Parameters:**
- `--folder_path`: Local directory containing files to upload
- `--repo_id`: Hugging Face repository identifier (org/repo-name)
- `--path_in_repo`: Subdirectory within the repository (default: "images")
- `--repo_type`: Repository type - "dataset" or "model" (default: "dataset")
- `--branch`: Target branch name (default: "main")

---

## 🛠️ Installation

### Prerequisites

- **Python 3.10+**
- **R 4.0+**
- **CUDA-capable GPU** (recommended for Grounding DINO, but not required)

### Python Setup

1. **Clone the repository:**
   ```bash
   git clone git@github.com:Imageomics/carabidae_beetle_processing.git
   cd carabidae_beetle_processing
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### R Setup

Install required R packages:
```r
install.packages(c("ggplot2", "dplyr", "ggpubr", "neonUtilities"))
```

### NEON API Token

For R script (`Figure6and10.R`):

1. **Create NEON account:** https://data.neonscience.org/
2. **Generate API token:** https://data.neonscience.org/data-api
3. **Save token to file:**
   ```bash
   echo "YOUR_TOKEN_HERE" > NEON_Token.txt
   ```

---

## 📊 Data Sources

### Hugging Face Datasets (Primary Access Point)

The processed datasets from this pipeline are available on Hugging Face along with the original data:

#### 1. Hawaii Beetles Dataset
**Repository:** [imageomics/Hawaii-beetles](https://huggingface.co/datasets/imageomics/Hawaii-beetles)

PUUM site beetle specimens including group images, individual crops, taxonomic identifications, and collection metadata.

#### 2. 2018 NEON Ethanol-preserved Ground Beetles Dataset
**Repository:** [imageomics/2018-NEON-beetles](https://huggingface.co/datasets/imageomics/2018-NEON-beetles)

Contains 2018 NEON beetle specimens with BeetlePalooza citizen science annotations:
- Individual beetle images (cropped from group images)
- Morphometric measurements (elytra length and width)
- Measurement coordinates with scale bar calibration
- Specimen metadata (genus, species, collection site)
- User annotations from multiple citizen scientists
- Quality-controlled measurement data


### CVAT Annotations

**File:** `2018_neon_beetles_bbox.xml`

Manual annotations created using CVAT (Computer Vision Annotation Tool) for 577 group images from 2018 NEON collections.

---

## 📝 Citation

### Citing This Software

If you use this code or methodology, please cite both this repository and our paper:

```bibtex
@software{Rayeed_Carabidae_Beetle_Processing_2025,
   author = {Rayeed, S M and Khurana, Mridul and East, Alyson and Campolongo, Elizabeth G. and Stevens, Samuel and Wu, Jiaman and Taylor, Graham W.},
   license = {MIT},
   month = nov,
   title = {{Carabidae Beetle Processing Pipeline}},
   url = {https://github.com/Imageomics/carabidae_beetle_processing},
   version = {1.0.0},
   year = {2025}
}
```

**Paper:** Coming Soon!

---

## Acknowledgments

This work was supported by both the [Imageomics Institute](https://imageomics.org) and the [AI and Biodiversity Change (ABC) Global Center](https://www.biodiversityai.org/). The Imageomics Institute is funded by the US National Science Foundation's Harnessing the Data Revolution (HDR) program under [Award #2118240](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2118240) (Imageomics: A New Frontier of Biological Information Powered by Knowledge-Guided Machine Learning). 
The ABC Global Center is funded by the US National Science Foundation under [Award No. 2330423](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2330423&HistoricalAwards=false) and Natural Sciences and Engineering Research Council of Canada under [Award No. 585136](https://www.nserc-crsng.gc.ca/ase-oro/Details-Detailles_eng.asp?id=782440). This code draws on research supported by the Social Sciences and Humanities Research Council.

S. Record and A. East were additionally supported by the US National Science Foundation's [Award No. 242918](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2429418&HistoricalAwards=false) (EPSCOR Research Fellows: NSF: Advancing National Ecological Observatory Network-Enabled Science and Workforce Development at the University of Maine with Artificial Intelligence) and by Hatch project Award #MEO-022425 from the US Department of Agriculture’s National Institute of Food and Agriculture. 

This material is based in part upon work supported by the [U.S. National Ecological Observatory Network (NEON)](https://www.neonscience.org/), a program sponsored by the [U.S. National Science Foundation (NSF)](https://www.nsf.gov/) and operated under cooperative agreement by [Battelle](https://www.battelle.org/). This material uses specimens and/or samples collected as part of the NEON Program.

Any opinions, findings and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the US National Science Foundation, the US Department of Agriculture, the Natural Sciences and Engineering Research Council of Canada, or the Social Sciences and Humanities Research Council.
