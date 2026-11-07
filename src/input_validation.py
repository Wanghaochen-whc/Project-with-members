"""Input validation logic for Dental OPG X-ray Project (Lab 05).

This module validates the input request against the project's input contract
before allowing prediction to proceed. It does NOT open or decode the image file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


# 状态优先级：Error > Warning > Pass
STATUS_RANK = {"pass": 0, "warning": 1, "error": 2}


def load_contract(path: str | Path) -> dict[str, Any]:
    """加载 input_contract.json"""
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def evaluate_rule(
    rule_name: str,
    observed_value: Any,
    passed: bool,
    severity: str,
    failure_action: str,
) -> dict[str, Any]:
    """评估单条规则并返回结果字典"""
    return {
        "rule": rule_name,
        "observed": str(observed_value), # 确保可序列化
        "status": "pass" if passed else severity,
        "action": "continue" if passed else failure_action,
    }


def combine_status(checks: list[dict[str, Any]]) -> str:
    """合并所有检查结果，返回最严重的状态 (error > warning > pass)"""
    if not checks:
        return "pass"
    # 找到 status 排名最高的（即数值最大的）
    worst_check = max(checks, key=lambda c: STATUS_RANK.get(c["status"], 0))
    return worst_check["status"]


def validate_request(
    request: dict[str, Any],
    contract: dict[str, Any],
    runtime_context: dict[str, Any],
) -> dict[str, Any]:
    """
    验证请求字段和运行时环境。
    
    注意：根据 Lab 05 要求，我们不打开 input_ref 指向的文件，
    也不解码图像字节。我们只检查请求中的元数据和路径字符串。
    """
    input_ref = request.get("input_ref", "")
    checks = []

    # 1. 结构规则：输入引用必须存在且非空 (Error)
    checks.append(evaluate_rule(
        "input_reference_present",
        input_ref,
        bool(input_ref and isinstance(input_ref, str) and len(input_ref.strip()) > 0),
        "error",
        contract.get("error_action", "reject_input"),
    ))

    # 2. 结构规则：文件扩展名必须是支持的图片格式 (Error)
    # 从合约中获取允许的后缀，如果没有则默认使用常见图片后缀
    allowed_extensions = contract.get("allowed_extensions", [".jpg", ".jpeg", ".png"])
    # 获取实际后缀并转为小写
    actual_ext = Path(input_ref).suffix.lower() if input_ref else ""
    ext_valid = actual_ext in allowed_extensions
    
    checks.append(evaluate_rule(
        "valid_image_extension",
        actual_ext,
        ext_valid,
        "error",
        contract.get("error_action", "reject_input"),
    ))

    # 3. 项目特定规则：来源路径检查 (Warning)
    # 检查路径是否包含预期的数据集关键词，例如 "Dental OPG"
    # 如果路径合法但不符合典型结构，标记为警告，建议人工审查
    expected_source_keyword = contract.get("expected_source_keyword", "Dental OPG")
    source_valid = expected_source_keyword in input_ref if input_ref else False
    
    checks.append(evaluate_rule(
        "source_path_convention",
        input_ref,
        source_valid,
        "warning", # 注意这里是 warning
        contract.get("warning_action", "route_for_review"),
    ))

    # 4. 运行时规则：预处理版本匹配 (Error)
    # 确保当前运行的代码使用的预处理 ID 与合约中定义的一致
    runtime_transform_id = runtime_context.get("transform_id")
    contract_transform_id = contract.get("transform_id")
    transform_matches = (runtime_transform_id == contract_transform_id)
    
    checks.append(evaluate_rule(
        "transform_version_match",
        runtime_transform_id,
        transform_matches,
        "error",
        contract.get("error_action", "reject_input"),
    ))

    # 合并状态
    final_status = combine_status(checks)
    
    # 根据最终状态决定动作
    action_map = {
        "pass": "continue_to_prediction",
        "warning": contract.get("warning_action", "route_for_review"),
        "error": contract.get("error_action", "reject_input"),
    }
    final_action = action_map.get(final_status, "reject_input")

    return {
        "request_id": request.get("request_id", "unknown"),
        "status": final_status,
        "action": final_action,
        "contract_version": contract.get("contract_version", "unknown"),
        "model_package": runtime_context.get("model_package", "unknown"),
        "transform_id": runtime_context.get("transform_id", "unknown"),
        "checks": checks,
    }


def route_request(
    request: dict[str, Any],
    validation: dict[str, Any],
    predict: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """
    路由请求：只有状态为 'pass' 时才会调用预测函数。
    Warning 和 Error 都会跳过预测。
    """
    # 只有当状态完全通过时，才调用预测
    prediction_called = validation["status"] == "pass"
    
    prediction_result = None
    if prediction_called:
        try:
            prediction_result = predict(request)
        except Exception as e:
            # 如果预测过程中出错，记录错误，但不改变验证状态
            prediction_result = {"error": str(e)}

    return {
        **validation, # 展开验证结果
        "prediction_called": prediction_called,
        "prediction": prediction_result,
    }
