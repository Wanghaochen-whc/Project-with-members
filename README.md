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
```
**Data**

Data description: See data/README.md

Two ways to obtain data:

- Automatic download via kagglehub (Requires valid Kaggle API token and stable network)

- Manual download from Kaggle, set local dataset path in code

**Run baseline**

python src/baseline_pipeline.py

**Output**

This command automatically generates the result file:
"reports/baseline_metrics.json"
The current baseline uses data from only two categories—"healthy" and "caries"—with a sample size of 80, resulting in an F1-score of 0.5833. It is important to consider the impact of class imbalance on the evaluation metrics.
```

## Lab 04: Inference Demo
This demo runs a single inference using the pre-trained baseline model from Lab 02 (no retraining).

### Run demo
```bash
python -m src.inference_demo --input-ref "C:/Users/w_h73/.cache/kagglehub/datasets/tommyngx/dental-opg-xray-2024/versions/1/Dental OPG XRAY Dataset/Dental OPG (Classification)/Caries/1.jpg"

**Output file**
reports/inference_demo.jsonl：Traceable inference record with request_id, prediction, action and metadata.

**Architecture diagram**
- Editable diagram: docs/inference_architecture.drawio
```

## Lab 05: Executable Input Assurance

Team Review & Discussion
1. Which requests reached the prediction result?
- Answer: Only the requests with a pass status (i.e., req-pass-001, which has a valid path containing the "Dental OPG" keyword for a normal X-ray) reached the prediction result and invoked the model.
2. Why did the warning request stop?
- Answer: According to our input contract (input_contract.json), when a warning rule is triggered (e.g., the path does not contain typical dataset characteristics), the configured action (warning_action) is route_for_review (forward to manual review). The validator intercepts it and does not automatically call the prediction to prevent unreliable medical advice from unknown data sources.
3. Which checks produced an error? How does severity priority affect the overall status?
- Answer: req-error-002 produced an error because the file extension was not .jpg/.png (triggering the valid_image_extension rule). The severity priority is error > warning > pass. This means that as long as one rule is judged as an error, regardless of whether other rules are pass or warning, the overall final_status will be forcibly judged as an error, thereby directly rejecting the input.
4. Which fields associate the validation decision with the generated trace information?
- Answer: The request_id field. It is created when the request is generated and runs through the entire process of validation, routing, and prediction, ensuring that each record in the JSONL log can be traced back to the same specific request attempt.
