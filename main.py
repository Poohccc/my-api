from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import datetime
import os

app = FastAPI(title="AI智能体枢纽 API (本地TXT文件版)", version="2.0")

# ==========================================
# ⚙️ 本地存储配置
# ==========================================
STORAGE_DIR = "memory_storage"

@app.on_event("startup")
def startup_event():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
        print(f"✅ 首次启动：已在本地创建存储文件夹 -> {STORAGE_DIR}/")
    else:
        print(f"✅ 正常启动：找到本地存储文件夹 -> {STORAGE_DIR}/")


# ==========================================
# 🎯 API 1：记忆黑盒 (修改为：支持覆盖存储与单独提取)
# ==========================================
class MemoryRequest(BaseModel):
    user_id: str                      # 用户的唯一ID
    action: str = Field(..., description="操作类型：'save' 表示覆盖存储，'extract' 表示提取数据") 
    current_query: Optional[str] = "" # 用户当前说的话（提取时可为空）


@app.post("/api/v1/memory/process")
async def process_memory(req: MemoryRequest):
    """
    根据 action 参数执行不同逻辑：
    - save: 覆盖写入该用户的 txt 文件
    - extract: 读取并返回该用户的 txt 文件内容
    """
    # 拼装这个用户的专属文件路径
    file_path = os.path.join(STORAGE_DIR, f"{req.user_id}.txt")
    
    # ---------------- 1. 存储逻辑 (覆盖) ----------------
    if req.action == "save":
        if not req.current_query:
            raise HTTPException(status_code=400, detail="保存模式下 current_query 不能为空")
            
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 格式化本次要保存的内容
        content_to_save = f"[{now_str}] 上一轮对话信息总结: {req.current_query}"
        
        try:
            # 使用 "w" 模式，直接覆盖写入
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_to_save)
                
            return {
                "status": "success",
                "message": "数据已覆盖存储",
                "context": content_to_save
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件写入失败: {str(e)}")

    # ---------------- 2. 提取逻辑 (读取) ----------------
    elif req.action == "extract":
        try:
            if os.path.exists(file_path):
                # 文件存在，读取内容
                with open(file_path, "r", encoding="utf-8") as f:
                    saved_context = f.read()
                return {
                    "status": "success",
                    "message": "数据提取成功",
                    "context": saved_context
                }
            else:
                # 文件不存在，返回空或提示
                return {
                    "status": "success",
                    "message": "暂无该用户的存储数据",
                    "context": ""
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")
            
    # ---------------- 3. 错误参数兜底 ----------------
    else:
        raise HTTPException(status_code=400, detail="非法的 action 参数，必须为 'save' 或 'extract'")


# ==========================================
# 🎯 API 2：预测模型路由 (保持不变)
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

# ==========================================
# 🚀 启动服务代码 (放在代码文件的最底部)
# ==========================================
if __name__ == "__main__":
    import uvicorn
    import os

    # 核心：获取云端的随机端口，如果是在本地则用 8000
    port = int(os.environ.get("PORT", 8000))

    # 注意：上面和这行前面，都有 4 个空格！
    uvicorn.run(app, host="0.0.0.0", port=port)
