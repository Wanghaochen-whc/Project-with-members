import os
import json
import random
from pathlib import Path
import kagglehub
import torch
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
import joblib

# ========== CONFIG ==========
RANDOM_SEED = 42
TOTAL_SAMPLES = 80
TEST_SIZE = 20
REPORT_PATH = Path("reports/baseline_metrics.json")
MODEL_CACHE_DIR = Path("cache")
CLF_PATH = MODEL_CACHE_DIR / "logreg.pkl"
TARGET_CLASSES = {
    "Healthy Teeth": 0,
    "Caries": 1
}
random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

# 全局缓存
_feature_model = None
_preprocess = None
_clf = None

def download_dataset():
    print("Downloading dataset via kagglehub...")
    dataset_path = kagglehub.dataset_download("tommyngx/dental-opg-xray-2024")
    print("Raw dataset path:", dataset_path)
    return Path(dataset_path)

def find_class_folders(root_path, target_names):
    """递归搜索，自动找到 Healthy Teeth / Caries，不管套多少层文件夹"""
    found = {}
    for target in target_names:
        matches = list(root_path.rglob(target))
        if len(matches) == 0:
            raise RuntimeError(f"Cannot find folder: {target}")
        found[target] = matches[0]
    return found

def sample_real_labels(raw_ds_path):
    img_ext = [".jpg", ".jpeg", ".png"]
    img_list = []
    folders = find_class_folders(raw_ds_path, TARGET_CLASSES.keys())
    for folder_name, label in TARGET_CLASSES.items():
        class_dir = folders[folder_name]
        for ext in img_ext:
            imgs = list(class_dir.rglob(f"*{ext}"))
            for p in imgs:
                img_list.append({"img_fullpath": str(p), "label": label})
    df_all = pd.DataFrame(img_list)
    print(f"Found {len(df_all)} images (Healthy + Caries)")
    df_healthy = df_all[df_all["label"] == 0]
    df_caries = df_all[df_all["label"] == 1]
    need_caries = TOTAL_SAMPLES // 2
    need_healthy = TOTAL_SAMPLES - need_caries
    sampled_healthy = df_healthy.sample(n=need_healthy, random_state=RANDOM_SEED)
    sampled_caries = df_caries.sample(n=need_caries, random_state=RANDOM_SEED)
    df = pd.concat([sampled_healthy, sampled_caries], ignore_index=True)
    print(f"Sampled {len(df)} images total (Healthy: {need_healthy}, Caries: {need_caries})")
    return df

def build_feature_extractor():
    resnet = models.resnet18(pretrained=True)
    resnet.eval()
    feature_model = torch.nn.Sequential(*list(resnet.children())[:-1])
    preprocess = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return feature_model, preprocess

def extract_features(df, feature_model, preprocess):
    feats = []
    labels = []
    for _, row in df.iterrows():
        img = Image.open(row["img_fullpath"]).convert("RGB")
        tensor = preprocess(img).unsqueeze(0)
        with torch.no_grad():
            feat = feature_model(tensor)
            feat_np = feat.squeeze().numpy()
            feats.append(feat_np)
        labels.append(row["label"])
    return feats, labels

def predict_one_image(img_path):
    global _feature_model, _preprocess, _clf
    if _feature_model is None or _preprocess is None:
        _feature_model, _preprocess = build_feature_extractor()
    if _clf is None:
        if not CLF_PATH.exists():
            raise RuntimeError("Classifier not trained! Run baseline_pipeline.py main first.")
        _clf = joblib.load(CLF_PATH)

    img = Image.open(img_path).convert("RGB")
    tensor = _preprocess(img).unsqueeze(0)
    with torch.no_grad():
        feat = _feature_model(tensor)
        feat_np = feat.squeeze().numpy().reshape(1, -1)
    pred = _clf.predict(feat_np)[0]
    if pred == 1:
        return "cavity"
    else:
        return "no cavity"

def main():
    raw_path = download_dataset()
    df = sample_real_labels(raw_path)
    train_df, test_df = train_test_split(
        df, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=df["label"]
    )
    print(f"Train: {len(train_df)}, Holdout eval: {len(test_df)}")
    feat_model, preproc = build_feature_extractor()
    X_train, y_train = extract_features(train_df, feat_model, preproc)
    X_test, y_test = extract_features(test_df, feat_model, preproc)
    clf = LogisticRegression(random_state=RANDOM_SEED, max_iter=500)
    clf.fit(X_train, y_train)

    # 保存模型，给inference_demo用
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
    joblib.dump(clf, CLF_PATH)

    y_pred = clf.predict(X_test)
    f1 = float(f1_score(y_test, y_pred))
    out = {
        "experiment": "Lab02 repeatable baseline",
        "baseline_type": "pretrained ResNet18 feature + Logistic Regression (no fine-tune)",
        "data_source": "kagglehub: tommyngx/dental-opg-xray-2024",
        "label_rule": "Caries=1, Healthy Teeth=0; other classes ignored",
        "random_seed": RANDOM_SEED,
        "total_samples": TOTAL_SAMPLES,
        "train_samples": len(train_df),
        "holdout_eval_samples": len(test_df),
        "main_metric": "f1_score",
        "f1_score": round(f1, 4),
        "important_note": "Only two classes (healthy / caries) used for this baseline."
    }
    os.makedirs(REPORT_PATH.parent, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"✅ Result saved to {REPORT_PATH}")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()