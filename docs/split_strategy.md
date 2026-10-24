# Split Strategy for Baseline Evaluation
Baseline type: 2. We use a pretrained model without extra training
Split method: random split
Total samples: 80
Evaluation hold-out samples: 20
Training samples (if applicable): 60
Which data is used for evaluation:
- The held-out evaluation set is separated before any model fitting.
- This subset is never used for tuning or selection.
Similarity to future real-world data:
The evaluation OPG X-ray images come from the same Kaggle dataset distribution as our small sampled data; they are clinical dental X-ray images for oral screening.
Limitation of this initial evaluation:
We only use two classes (Healthy Teeth and Caries) from the full dataset, ignoring impacted teeth, fractures and infection. The evaluation set is small (20 images). ResNet18 is pre-trained on natural images and not fine-tuned on dental X-rays. All images are from one single public dataset, which may not represent X-ray machines and patient populations from real hospitals.