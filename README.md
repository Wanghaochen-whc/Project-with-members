# Project-with-members
- Team Name：Peace
- Team members：Wang Haochen; Kuang Zanquan; Gao Zhiyuan; Adekuoroye Sola emmanuel.
- The team will communicate via Telegram groups or other mutually agreed spaces.
- We hope to help oral screening personnel use oral photos to identify possible tooth decay on teeth.(我们希望帮助口腔筛查人员使用口腔照片来识别牙齿上可能存在的蛀牙。)

## Lab 02 - Repeatable Baseline
Python version: 3.10
### Setup
Install dependencies:
```bash
git statuspip install -r requirements.txt

Data
Data description: See data/README.md
Two ways to obtain data:
Automatic download via kagglehub (Requires valid Kaggle API token and stable network)
Manual download from Kaggle, set local dataset path in code

Run baseline
python src/baseline_pipeline.py

Output
This command automatically generates the result file:
"reports/baseline_metrics.json"
The current baseline uses data from only two categories—"healthy" and "caries"—with a sample size of 80, resulting in an F1-score of 0.5833. It is important to consider the impact of class imbalance on the evaluation metrics.