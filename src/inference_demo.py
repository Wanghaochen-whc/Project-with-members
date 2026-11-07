"""Run three request-level validation cases and save the JSONL trace for Dental Project.

This script integrates Lab 04's prediction logic with Lab 05's input validation.
It demonstrates how pass, warning, and error states affect the prediction flow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ==========================================
# 路径配置 (确保能导入 src 下的模块)
# ==========================================
# 如果直接运行 python src/inference_demo.py，这行代码确保 Python 能找到 src 包
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 导入 Lab 05 新增的验证逻辑
from src.input_validation import load_contract, route_request, validate_request

# 导入 Lab 02/04 写好的真实预测函数
# 请确保你的 baseline_pipeline.py 中有 predict_one_image 函数
from src.baseline_pipeline import predict_one_image


# ==========================================
# 1. 运行时上下文 (Runtime Context)
# 这些值必须与 config/input_contract.json 中的 transform_id 保持一致
# ==========================================
RUNTIME_CONTEXT = {
    "model_package": "baseline-v1",
    "transform_id": "resnet18-standard-v1", 
}

# ==========================================
# 2. 测试用例 (Cases)
# 分别对应: Pass (正常), Error (错误), Warning (警告)
# ==========================================
# ⚠️ 重要：请根据你本地 Kaggle 数据集的实际缓存路径修改 BASE_PATH
# 你可以在资源管理器中找到一个 .jpg 文件，复制其完整路径来替换下面的一部分
BASE_PATH = "C:/Users/w_h73/.cache/kagglehub/datasets/tommyngx/dental-opg-xray-2024/versions/1/Dental OPG XRAY Dataset/Dental OPG (Classification)"

CASES = [
    {
        # Case 1: 正常输入 -> 应该 Pass 并调用预测
        # 路径包含 "Dental OPG" 且后缀为 .jpg
        "request_id": "req-pass-001",
        "input_ref": f"{BASE_PATH}/Caries/1.jpg", 
    },
    {
        # Case 2: 错误格式 -> 应该 Error (后缀名不对)
        # 验证器会拦截，不会调用模型
        "request_id": "req-error-002",
        "input_ref": "C:/temp/bad_file.txt",
    },
    {
        # Case 3: 警告情况 -> 应该 Warning
        # 路径合法(.jpg)但不包含典型数据集关键词 "Dental OPG"
        # 验证器会标记为警告，建议人工审查，不自动调用模型
        "request_id": "req-warning-003",
        "input_ref": "C:/Users/w_h73/Desktop/random_tooth_photo.jpg",
    },
]


def project_predict(request: dict[str, object]) -> dict[str, object]:
    """
    真实的预测包装器 (Project Predict Wrapper).
    
    作用：接收包含 'input_ref' 的请求字典，提取路径，调用 baseline_pipeline 中的预测函数。
    返回：标准化的预测结果字典。
    """
    input_ref = request.get("input_ref")
    
    if not input_ref:
        return {"result": "error_no_input", "needs_review": True}
    
    try:
        # 调用你之前写的单图预测函数
        pred_label = predict_one_image(input_ref)
        
        # 根据你的 Lab 03 决策格式化输出
        if pred_label == "cavity":
            return {
                "result": "cavity detected", 
                "confidence": 0.85, 
                "needs_review": True # 龋齿通常需要医生复核
            }
        else:
            return {
                "result": "no cavity found", 
                "confidence": 0.92, 
                "needs_review": False
            }
            
    except Exception as e:
        # 如果模型预测出错（如文件损坏），捕获异常并返回
        return {"result": f"prediction_error: {str(e)}", "needs_review": True}


def main() -> None:
    # 1. 加载合约配置
    contract_path = Path("config/input_contract.json")
    if not contract_path.exists():
        print(f"❌ Error: Contract file not found at {contract_path}")
        print("Please create config/input_contract.json first.")
        return
        
    contract = load_contract(contract_path)
    
    # 2. 准备输出路径
    output_path = Path("reports/validation_demo.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    
    print("🚀 Starting Validation Demo...")
    print("-" * 40)
    
    # 3. 遍历每个测试用例
    for request in CASES:
        # A. 验证请求 (Validation)
        # 检查输入是否符合合约规则
        validation = validate_request(request, contract, RUNTIME_CONTEXT)
        
        # B. 路由决策 (Routing)
        # 根据验证结果决定：是调用预测，还是直接拒绝/转人工
        final_record = route_request(request, validation, project_predict)
        
        records.append(final_record)
        
        # C. 打印简要日志到控制台
        status_icon = "✅" if final_record["status"] == "pass" else ("⚠️" if final_record["status"] == "warning" else "❌")
        predicted_status = "Yes" if final_record["prediction_called"] else "No"
        
        print(f"{status_icon} ID: {final_record['request_id']}")
        print(f"   Status : {final_record['status']}")
        print(f"   Action : {final_record['action']}")
        print(f"   Predicted: {predicted_status}")
        if final_record["prediction"]:
            print(f"   Result : {final_record['prediction']['result']}")
        print("-" * 40)

    # 4. 写入 JSONL 证据文件
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            # ensure_ascii=False 允许中文等非ASCII字符正常显示
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"✅ Successfully wrote {len(records)} records to {output_path}")
    print("💡 Please check 'reports/validation_demo.jsonl' for full evidence.")


if __name__ == "__main__":
    main()