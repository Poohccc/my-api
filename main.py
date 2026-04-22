from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime
import os

app = FastAPI(title="AI智能体枢纽 API (本地TXT文件版)", version="2.0")

# ==========================================
# ⚙️ 本地存储配置
# ==========================================
# 我们在本地建一个文件夹，专门用来放 txt 记忆文件
STORAGE_DIR = "memory_storage"


# 🚀 启动时自动检查并创建文件夹
@app.on_event("startup")
def startup_event():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
        print(f"✅ 首次启动：已在本地创建存储文件夹 -> {STORAGE_DIR}/")
    else:
        print(f"✅ 正常启动：找到本地存储文件夹 -> {STORAGE_DIR}/")


# ==========================================
# 🎯 API 1：记忆黑盒 (用 TXT 文件代替数据库)
# ==========================================
class MemoryRequest(BaseModel):
    user_id: str  # 用户的唯一ID，将作为 txt 的文件名
    current_query: str  # 用户当前说的话


@app.post("/api/v1/memory/process")
async def process_memory(req: MemoryRequest):
    """
    接收 user_id，读取对应的 txt 文件，追加新对话，再保存回 txt 文件。
    """
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_message = f"[{now_str}] 用户输入: {req.current_query}"

    # 拼装这个用户的专属文件路径，例如: memory_storage/user_123.txt
    file_path = os.path.join(STORAGE_DIR, f"{req.user_id}.txt")
    merged_context = ""

    try:
        # 1. 查：看看这个用户的 txt 文件存不存在
        if os.path.exists(file_path):
            # 如果存在，把以前的聊天记录读出来
            with open(file_path, "r", encoding="utf-8") as f:
                old_history = f.read()
            # 把新话拼在老话后面
            merged_context = f"{old_history}\n{new_message}"
        else:
            # 如果不存在，说明是新用户，直接用新话
            merged_context = new_message

        # 2. 存：把最新的完整聊天记录覆盖写入 txt 文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(merged_context)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件读写失败: {str(e)}")

    # 3. 返：把拼好的长文本返回给调用者
    return {
        "status": "success",
        "merged_context": merged_context
    }


# ==========================================
# 🎯 API 2：预测模型路由 (保持不变，无需数据库)
# ==========================================
class PredictRequest(BaseModel):
    product_id: str
    sales: List[float]
    features: Optional[Dict[str, Any]] = {}


@app.post("/api/v1/predict/route")
async def route_and_predict(req: PredictRequest):
    sales_length = len(req.sales)
    features_exist = req.features is not None and len(req.features) > 0
    selected_model_name = ""

    if features_exist:
        selected_model_name = "机器学习 (Machine Learning)"
    elif sales_length >= 12:
        selected_model_name = "深度学习 (Deep Learning)"
    elif 3 <= sales_length < 12:
        selected_model_name = "移动平均 (Moving Average)"
    else:
        selected_model_name = "简单平均 (Simple Average)"

    # 模拟预测结果
    mock_prediction = sum(req.sales) / len(req.sales) if sales_length > 0 else 0.0
    prediction_result = round(mock_prediction * 1.05, 2)

    return {
        "status": "success",
        "route_info": {"selected_model": selected_model_name},
        "prediction_result": prediction_result
    }

