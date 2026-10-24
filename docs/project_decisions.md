# Project decisions
## Lab 03 — Acceptance

### Decision after the baseline
Decision: Continue
Reason: Based on the baseline F1 result and the important limitation (small 80-image sample, ResNet18 not fine-tuned on dental X-rays), we decided to continue the project, but keep the scope limited to binary classification: only distinguish healthy teeth vs caries on OPG X-ray images. We will not attempt grading of caries severity at this stage.

### Required behavior
- Normal input: A clear, properly cropped dental OPG X-ray.
  System output: Binary prediction (Caries / Healthy) + model confidence score.
  Next user action: The screening clinician reviews the AI suggestion together with the X-ray.
- Invalid input: Blurry photo, non-dental image, corrupted file, wrong scan type.
  System output: Reject input, return message "Image is not a valid OPG dental X-ray".
  Next user action: Upload a qualified dental X-ray again.
- Valid input with an uncertain result: Confidence near the decision boundary.
  System output: Mark as uncertain.
  Next user action: Forward this case to a dentist for manual review (human fallback).

### One quality that matters
Clinician trust / low false-negative rate (missing caries is clinically dangerous).

### One acceptance check
- Important failure: Miss existing caries (false negative: real caries predicted as healthy).
- Metric that would show this failure: False negative rate (FNR).
- Preliminary acceptance threshold: Below 10%.
- Where will we check it? Held-out clinical evaluation set.
- Why this number for now? In oral screening, missing a caries lesion carries clinical risk; we accept a small controlled rate of misses.
- Evidence still missing: Larger labelled multi-source dental X-ray dataset from different hospitals.

### Failure cases
| Area | What could go wrong and why it matters | How would we notice it? | Planned response |
| --- | --- | --- | --- |
| Data or input | X-ray is overexposed / blurry, hides caries | Input quality checker flags low-contrast images | Reject image and prompt re-scan |
| Model behavior | Caries present but model says healthy (false negative, matches our acceptance-check failure) | Evaluation FNR rises above threshold | Send this case automatically to dentist review; retrain model later with these hard samples |
| Integration or workflow | Pipeline crashes and does not return any prediction | Log shows runtime error, empty output | Show friendly error to user; keep original X-ray for manual review |