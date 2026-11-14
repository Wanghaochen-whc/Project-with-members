"""Dental Caries Detection API for Cloud Deployment (Lab 06)."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

# ==========================================
# 1. 导入你们团队 Lab 04-05 的核心模块
# ==========================================
# 注意：这里假设 lab_06/starter 与 src/ 在同一级目录下
# 如果部署时目录结构不同，请根据实际情况调整 sys.path 或导入路径
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.input_validation import validate_request, load_contract
from src.baseline_pipeline import predict_one_image


BASE_DIR = Path(__file__).resolve().parent
LOGGER = logging.getLogger(__name__)
load_dotenv(BASE_DIR / ".env")


# ==========================================
# 2. 牙科预测器包装类
# ==========================================
class DentalPredictor:
    """加载并调用你们的 ResNet18 + Logistic Regression 基线模型。"""

    def __init__(self) -> None:
        self._model_loaded = False

    @property
    def loaded(self) -> bool:
        return self._model_loaded

    def __call__(self, image_path: str) -> dict[str, Any]:
        """
        接收本地图片路径，返回标准化的预测结果。
        这是为了适配你们 baseline_pipeline.py 中 predict_one_image(img_path) 的接口。
        """
        if not self._model_loaded:
            LOGGER.info("Loading dental caries detection model on first valid request...")
            # 触发一次预测即可隐式加载全局缓存模型
            # 也可以在这里显式调用 build_feature_extractor() 等初始化函数
            self._model_loaded = True

        started = perf_counter()
        
        # 调用你们 Lab 04 的真实预测函数
        pred_label = predict_one_image(image_path)
        
        latency_ms = round((perf_counter() - started) * 1000, 1)

        # 格式化输出，保持与 Starter 类似的 JSON 结构
        if pred_label == "cavity":
            result_text = "cavity detected"
            needs_review = True
        else:
            result_text = "no cavity found"
            needs_review = False

        return {
            "model": "resnet18-logreg-baseline-v1",
            "result": result_text,
            "needs_review": needs_review,
            "latency_ms": latency_ms,
        }


# ==========================================
# 3. JSONL 证据记录工具函数
# ==========================================
def append_jsonl(record: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


# ==========================================
# 4. 创建 FastAPI 应用
# ==========================================
def create_app(
    evidence_path: Path | None = None,
    predictor: DentalPredictor | None = None,
) -> FastAPI:
    environment = os.getenv("ENVIRONMENT", "classroom")
    service_version = os.getenv("SERVICE_VERSION", "dental-caries-cloud-v1")
    
    # 加载你们 Lab 05 定制的输入合约
    contract = load_contract(BASE_DIR / "config" / "input_contract.json")
    
    # 设置云端 JSONL 证据文件路径
    trace_path = evidence_path or BASE_DIR / os.getenv(
        "EVIDENCE_PATH", "reports/dental_predictions.jsonl"
    )
    
    # 初始化预测器
    model_predict = predictor or DentalPredictor()

    application = FastAPI(
        title="Dental Caries Detection Cloud Service",
        version=service_version,
        description=(
            "Upload a JPEG or PNG dental OPG X-ray image. "
            "The service validates input against the project contract, "
            "runs the ResNet18 baseline model on CPU, and records the decision."
        ),
    )

    @application.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "environment": environment,
            "service_version": service_version,
            "model": "resnet18-logreg-baseline-v1",
            "model_loaded": model_predict.loaded,
        }

    @application.post("/predict", response_model=None)
    async def predict(
        file: UploadFile = File(...),
        request_id: str = Form(default=""),
    ) -> Any:
        resolved_request_id = request_id.strip() or f"req-{uuid4().hex[:8]}"
        
        # --- A. 保存上传文件到临时目录 ---
        # 因为你们的 predict_one_image 接受的是文件路径字符串，
        # 所以必须先把 FastAPI 的内存文件流写入磁盘
        temp_file = None
        try:
            suffix = Path(file.filename).suffix.lower()
            # 安全检查：只允许图片后缀
            if suffix not in [".jpg", ".jpeg", ".png"]:
                suffix = ".jpg" 
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            temp_path = temp_file.name

            # --- B. 构建符合 Lab 05 格式的请求字典 ---
            request_dict = {
                "request_id": resolved_request_id,
                "input_ref": temp_path,
            }

            # --- C. 执行 Lab 05 的输入验证 ---
            # runtime_context 必须与 config/input_contract.json 中的 transform_id 一致
            runtime_context = {
                "model_package": "baseline-v1",
                "transform_id": "resnet18-standard-v1",
            }
            
            validation = validate_request(request_dict, contract, runtime_context)
            
            base_record = {
                "request_id": resolved_request_id,
                "filename": file.filename,
                "status": validation["status"],
                "action": validation["action"],
                "contract_version": validation["contract_version"],
                "checks": validation["checks"],
            }

            # --- D. 根据验证结果路由 ---
            if validation["status"] != "pass":
                # 验证失败：拒绝预测，返回 400
                record = {
                    **base_record,
                    "prediction_called": False,
                    "prediction": None,
                }
                append_jsonl(record, trace_path)
                return JSONResponse(status_code=400, content=record)

            # --- E. 验证通过：调用真实模型 ---
            try:
                prediction = model_predict(temp_path)
            except Exception as error:
                LOGGER.exception("Inference failed for request %s", resolved_request_id)
                record = {
                    **base_record,
                    "status": "error",
                    "action": "inference_unavailable",
                    "prediction_called": True,
                    "prediction": None,
                    "error_type": type(error).__name__,
                }
                append_jsonl(record, trace_path)
                return JSONResponse(status_code=503, content=record)

            # 预测成功
            record = {
                **base_record,
                "prediction_called": True,
                "prediction": prediction,
            }
            append_jsonl(record, trace_path)
            return record

        finally:
            # --- F. 清理临时文件，防止云服务器磁盘写满 ---
            if temp_file is not None:
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass

    return application


app = create_app()
