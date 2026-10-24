# Data README
Dataset name: Dental OPG X-ray 2024
Source: Kaggle https://www.kaggle.com/datasets/tommyngx/dental-opg-xray-2024
License: not yet confirmed

Folder structure:
data/
# We do NOT store image files in this repo. No local image folder is required.

How to get data:
Data will be downloaded automatically by kagglehub when running src/baseline_pipeline.py.
A valid Kaggle API token must be configured on your machine before execution.
Dataset: https://www.kaggle.com/datasets/tommyngx/dental-opg-xray-2024

Preprocessing:
No extra manual preprocessing required before running the baseline pipeline.

Labels are derived from folder names: "Healthy Teeth" = 0, "Caries" = 1. We ignore the other 4 categories for this binary baseline.

