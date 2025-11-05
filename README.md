# Carabidae Beetle Processing Pipeline

**Automated Processing and Quality Assessment for Beetle Morphometric Data**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Pipeline Components](#pipeline-components)
- [Installation](#installation)
- [Usage](#usage)
  - [1. Individual Beetle Extraction](#1-individual-beetle-extraction)
  - [2. Zero-Shot Object Detection](#2-zero-shot-object-detection)
  - [3. Quality Control and Validation](#3-quality-control-and-validation)
  - [4. Data Visualization](#4-data-visualization)
- [Data Sources](#data-sources)
- [Citation](#citation)

---

## 🎯 Overview

This repository contains a complete pipeline for processing, analyzing, and validating beetle specimen images and morphometric measurements from the NEON (National Ecological Observatory Network) and BeetlePalooza datasets. The project focuses on **Carabidae** (ground beetles) and implements:

1. **Automated beetle detection and cropping** from group images using CVAT annotations and zero-shot object detection
2. **Morphometric trait extraction** including elytra length and width measurements
3. **Inter-annotator agreement analysis** comparing measurements between human annotators
4. **Human vs. automated system validation** evaluating algorithmic measurements against manual measurements
5. **Species distribution visualization** for PUUM (Pu'u Maka'ala Natural Area Reserve, Hawaii) site data

The pipeline integrates computer vision (Grounding DINO), traditional image processing, and statistical validation to create a robust, reproducible workflow for entomological specimen digitization.

---

## 📁 Project Structure

```
carabidae_beetle_processing/
├── 2018_neon_beetles_bbox.xml                      # CVAT annotations (577 images)
├── 2018_neon_beetles_get_individual_images.py      # Crop beetles from group images
├── resizing_individual_beetle_images.py            # Resize individual images with uniform scaling
├── grounding_dion.ipynb                            # Zero-shot object detection pipeline
├── upload_dataset_to_hf.py                         # Upload datasets to Hugging Face
├── InterAnnotator.py                               # Inter-annotator agreement analysis
├── CalipersVsToras.py                              # Human vs. automated measurement comparison
├── Figure6and10.R                                  # NEON data analysis and visualization
├── .gitignore                                      # Git ignore patterns
├── LICENSE                                         # MIT License
├── CITATION.cff                                    # Citation metadata
├── requirements.txt                                # Python dependencies
└── README.md                                       # This file
```

---

## 🔬 Pipeline Components

### 1. **Image Annotation and Extraction**

**File:** `2018_neon_beetles_bbox.xml`

CVAT (Computer Vision Annotation Tool) annotations containing:
- 577 annotated images
- Bounding box coordinates for individual beetles in group images
- Image dimensions (5568 × 3712 pixels)
- Created: April 2025

**Format:**
```xml
<image id="0" name="group_images/A00000001831.jpg" width="5568" height="3712">
    <box label="bbox" xtl="2051.88" ytl="1881.84" xbr="2417.17" ybr="2473.22"/>
    ...
</image>
```

### 2. **Traditional Bounding Box Cropping**

**Script:** `2018_neon_beetles_get_individual_images.py`

Extracts individual beetle specimens from annotated group images using CVAT XML annotations.

**Features:**
- Parses CVAT XML format
- Extracts bounding box coordinates
- Crops individual specimens with optional padding
- Saves as separate PNG files with specimen numbering
- Progress tracking with tqdm

**Key Functions:**
- `parse_cvat_annotations(xml_path)`: Parse CVAT XML and extract image metadata
- `crop_and_save_images(images_data, images_dir, output_dir, padding)`: Crop and save specimens

### 3. **Image Resizing with Uniform Scaling**

**Script:** `resizing_individual_beetle_images.py`

Resizes individual beetle specimen images to match BeetlePalooza's resized group images using uniform scaling factors.

**Purpose:**
- Aligns individual specimen images with the resolution of BeetlePalooza's processed group images
- Ensures morphometric measurements made on resized images can be accurately applied to individual specimens
- Uses uniform scaling (average of x and y scale factors) for consistency

**Workflow:**
1. Calculate uniform scaling factors between original and BeetlePalooza resized group images
2. Save scaling factors to JSON for reference and reproducibility
3. Apply uniform scaling to all individual specimen images
4. Generate processing summary with statistics

### 4. **Dataset Upload to Hugging Face**

**Script:** `upload_dataset_to_hf.py`

Utility script for uploading processed beetle datasets to Hugging Face Hub for public access and reproducibility.

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

### 5. **Zero-Shot Object Detection**

**Notebook:** `grounding_dion.ipynb`

Advanced pipeline using **Grounding DINO** for automated beetle detection and segmentation.

**Workflow:**
1. Load beetle measurements from BeetlePalooza dataset
2. Initialize Grounding DINO model (IDEA-Research/grounding-dino-base)
3. For each image:
   - Detect beetles using text prompt ("a beetle")
   - Filter detections based on adaptive area thresholds
   - Verify detections contain elytra measurement points
   - Apply Non-Maximum Suppression (NMS) to remove duplicates
   - Select best bounding box (largest area with highest confidence)
4. Save individual beetle images and CSV metadata

### 6. **Inter-Annotator Agreement**

**Script:** `InterAnnotator.py`

Quantifies measurement consistency between multiple human annotators for continuous morphometric traits.

**Analysis:**
- Compares three annotator pairs:
  - Annotator A vs. Annotator B
  - Annotator B vs. Annotator C
  - Annotator C vs. Annotator A

**Metrics Computed:**
- **RMSE** (Root Mean Square Error): Overall measurement disagreement
- **R² Score**: Correlation strength between annotators
- **Average Bias**: Systematic over/under-measurement tendencies

**Output:**
- `InterAnnotatorAgreement.pdf`: Three-panel scatter plot
- Console report with detailed metrics

### 7. **Human vs. Automated System Validation**

**Script:** `CalipersVsToras.py`

Evaluates TORAS measurement annotations performance against human expert measurements using calipers (gold standard).

**Comparisons:**
- Annotator A vs. Automated System
- Annotator B vs. Automated System
- Annotator C vs. Automated System
- Average Human vs. Automated System

**Metrics:**
- RMSE, R², Average Bias (same as inter-annotator analysis)

**Output:**
- `CalipersVsToras.pdf`: Comparison plots
- Quantitative performance metrics


### 8. **NEON Data Analysis and Visualization**

**Script:** `Figure6and10.R`

Comprehensive analysis of NEON beetle data from PUUM site (Hawaii) with BeetlePalooza integration.

**Data Sources:**
- **NEON API**: DP1.10022.001 (Ground beetle sequences DNA barcode)
- **BeetlePalooza**: Citizen science measurement data
- Site: PUUM (Pu'u Maka'ala Natural Area Reserve, Hawaii)

**Outputs:**
- `BeetlePUUM_abundance.png`: Species abundance with imaging status (Not Imaged vs. Imaged)
- Merged dataset combining NEON taxonomic data with BeetlePalooza measurements

**R Libraries:**
- `ggplot2`: Data visualization
- `dplyr`: Data manipulation
- `ggpubr`: Publication-ready themes
- `neonUtilities`: NEON API interface

---

## 🛠️ Installation

### Prerequisites

- **Python 3.8+** (for Python scripts and notebooks)
- **R 4.0+** (for R scripts)
- **Git** (for version control)
- **CUDA-capable GPU** (recommended for Grounding DINO, but not required)

### Python Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mridulk97/carabidae_beetle_processing.git
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

## 🚀 Usage

### 1. Individual Beetle Extraction

Extract individual beetles from group images using CVAT annotations:

```bash
python 2018_neon_beetles_get_individual_images.py \
    --xml_file 2018_neon_beetles_bbox.xml \
    --images_dir /path/to/group_images/ \
    --output_dir /path/to/individual_beetles/ \
```

**Parameters:**
- `--xml_file`: Path to CVAT XML annotation file
- `--images_dir`: Directory containing original group images
- `--output_dir`: Output directory for cropped beetle images
- `--padding`: (OPTIONAL) Additional pixels around bounding box (default: 0)

**Output:**
- Individual beetle images named: `{original_name}_specimen_{N}.png`

### 2. Zero-Shot Object Detection

Run the Jupyter notebook for automated beetle detection:

```bash
jupyter notebook grounding_dion.ipynb
```

**Key Configuration Variables** (modify in notebook):

```python
# Data paths
df_bm = pd.read_csv("BeetleMeasurements_updated_merged_uniqueBeetles.csv")
image_dir = "/path/to/resized_images/"
outdir = "/path/to/individual_images/"

# Model parameters
model_id = "IDEA-Research/grounding-dino-base"
text = "a beetle."
box_threshold = 0.2
text_threshold = 0.2
iou_threshold = 0.6
padding = 0.1
```

### 3. Quality Control and Validation

#### Inter-Annotator Agreement

```bash
python InterAnnotator.py
```

**Configuration** (edit in script):
```python
DATA_PATH = "data/traits.csv"
OUTPUT_FIG = "InterAnnotatorAgreement.pdf"

ANNOTATOR_PAIRS = [
    ('AnnotatorA_length', 'AnnotatorB_length', 'Title', 'Label A', 'Label B'),
    # ... add more pairs
]

LIM_MIN, LIM_MAX = 0.15, 0.65  # Axis limits for consistency
```

**Output:**
```
📊 === Inter-Annotator Agreement Metrics ===
Annotator A vs Annotator B:
   RMSE       = 0.0234
   R² Score   = 0.9567
   Avg. Bias  = -0.0012

📈 === Average Across All Annotator Pairs ===
   RMSE (mean)  = 0.0245
   R² (mean)    = 0.9523
   Bias (mean)  = -0.0008
```

#### Human vs. Automated System

```bash
python CalipersVsToras.py
```

**Configuration** (edit in script):
```python
DATA_PATH = "data/traits.csv"
OUTPUT_FIG = "CalipersVsToras.pdf"

ANNOTATOR_PAIRS = [
    ('AnnotatorA_length', 'System_length', 'Title', 'Annotator A'),
    # ... add more pairs
]
```

**Output:**
- PDF figure with scatter plots
- Metrics comparing each annotator to automated system
- Average human vs. system metrics

### 4. Data Visualization

Run R script for NEON data analysis:

```bash
Rscript Figure6and10.R
```

**Configuration** (edit in script):
```r
# Set working directory
setwd("/path/to/project/")

# NEON configuration
Beetle_dpID <- "DP1.10022.001"
NEON_TOKEN <- read.delim("NEON_Token.txt", header = FALSE)[1, 1]

# BeetlePalooza data
meta_Plooza <- read.csv("./BeetlePalooza_Data/individual_metadata.csv")
```

**Workflow:**
1. Load NEON data via API for PUUM site
2. Filter and merge parataxonomist/expert identifications
3. Load BeetlePalooza metadata
4. Merge datasets by specimen ID
5. Create species abundance plots with imaging status
6. Save publication-ready figures

**Output:**
- `BeetlePUUM_abundance.png`: Species distribution bar chart
- Merged dataset with taxonomic and measurement data

---

## 📊 Data Sources

### Hugging Face Datasets (Primary Access Point)

The processed datasets from this pipeline are available on Hugging Face:

#### 1. Hawaii Beetles Dataset
**Repository:** [imageomics/Hawaii-beetles](https://huggingface.co/datasets/imageomics/Hawaii-beetles)

Contains BeetlePalooza citizen science data including:
- Individual beetle images (cropped and processed)
- Morphometric measurements (elytra length and width)
- Measurement coordinates with scale bar calibration
- Specimen metadata (genus, species, collection information)
- Site environmental data
- User annotations from multiple annotators

#### 2. 2018 NEON Beetles Dataset
**Repository:** [imageomics/2018-NEON-beetles](https://huggingface.co/datasets/imageomics/2018-NEON-beetles)

Contains NEON beetle data from 2018 including:
- Group beetle images from PUUM site
- CVAT bounding box annotations
- Individual beetle crops
- Taxonomic identifications
- Collection metadata



### CVAT Annotations

**File:** `2018_neon_beetles_bbox.xml`

Manual annotations created using CVAT (Computer Vision Annotation Tool) for 577 group images from 2018 NEON collections.

---

## 📝 Citation

### Citing This Software

If you use this code or methodology, please cite:

```bibtex
@software{rayeed2025carabidae,
  title = {Carabidae Beetle Processing Pipeline: Automated Morphometric Analysis and Quality Assessment},
  author = {Rayeed, S M and Khurana, Mridul and East, Alyson and 
            Fluck, Isadora E. and Campolongo, Elizabeth G. and Stevens, Samuel and 
            Zarubiieva, Iuliia and Lowe, Scott C. and Denslow, Michael W. and 
            Donoso, Evan D. and Wu, Jiaman and Ramirez, Michelle and 
            Baiser, Benjamin and Stewart, Charles V. and Mabee, Paula and 
            Berger-Wolf, Tanya and Karpatne, Anuj and Lapp, Hilmar and 
            Guralnick, Robert P. and Taylor, Graham W. and Record, Sydne},
  year = {2025},
  version = {1.0.0},
  institution = {Imageomics and ABC Institute},
  url = {https://github.com/Imageomics/carabidae_beetle_processing},
}
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

This work was supported by both the Imageomics Institute and the AI and Biodiversity Change (ABC) Global Center. The Imageomics Institute is funded by the US National Science Foundation's Harnessing the Data Revolution (HDR) program under Award #2118240 (Imageomics: A New Frontier of Biological Information Powered by Knowledge-Guided Machine Learning). The ABC Global Center is funded by the US National Science Foundation under Award No. 2330423 and Natural Sciences and Engineering Research Council of Canada under Award No. 585136.

S. Record and A. East were additionally supported by the US National Science Foundation's Award No. 242918 and by Hatch project Award #MEO-022425 from the US Department of Agriculture’s National Institute of Food and Agriculture.

This material is based in part upon work supported by the National Ecological Observatory Network (NEON), a program sponsored by the U.S. National Science Foundation (NSF) and operated under cooperative agreement by Battelle.

Any opinions, findings and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the US National Science Foundation, the US Department of Agriculture, or Natural Sciences and Engineering Research Council of Canada.


---

**Last Updated:** November 2025  
**Version:** 1.0  
**Status:** Active Development