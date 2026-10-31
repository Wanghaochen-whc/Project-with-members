import kagglehub
from pathlib import Path
dataset_path = Path(kagglehub.dataset_download("tommyngx/dental-opg-xray-2024"))
# 找Caries文件夹下随便一张图
caries_folder = list(dataset_path.rglob("Caries"))[0]
one_img = list(caries_folder.glob("*.jpg"))[0]
print(one_img)