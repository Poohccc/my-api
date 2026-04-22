from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import datetime
import pymysql
import os

app = FastAPI(title="AI智能体枢纽 API (带记忆黑盒)", version="2.0")

# ==========================================
# ⚙️ 数据库连接配置 (从 Railway 环境变量读取)
# ==========================================
# 当你在 Railway 部署时，填入环境变量。本地测试时可以填默认值。
DB_HOST = os.getenv("MYSQLHOST", "你的数据库IP或域名")
DB_PORT = int(os.getenv("MYSQLPORT", 3306))
DB_USER = os.getenv("MYSQLUSER", "你的数据库用户名")
DB_PASSWORD = os.getenv("MYSQLPASSWORD", "你的数据库密码")
DB_NAME = os.getenv("MYSQLDATABASE", "你的数据库名")

def get_db_connection():
    """建立并返回一个数据库连接"""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# 🚀 启动时自动建表（如果表不存在的话，免去你手动建表的烦恼）
@app.on_event("startup")
def startup_event():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id VARCHAR(255) PRIMARY KEY,
                    history_text TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
        conn.commit()
        conn.close()
        print("✅ 数据库表 user_memory 检查/创建成功！")
    except Exception as e:
        print(f"⚠️ 数据库连接或建表失败，请检查环境变量配置: {e}")


# ==========================================
# 🎯 API 1：记忆黑盒 (自动读写数据库)
# ==========================================
class MemoryRequest(BaseModel):
    user_id: str           # 用户的唯一ID
    current_query: str     # 用户当前说的话

@app.post("/api/v1/memory/process")
async def process_memory(req: MemoryRequest):
    """
    接收 user_id 和新问题，内部自动查数据库、拼接、存数据库，返回完整上下文。
    """
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_message = f"[{now_str}] 用户输入: {req.current_query}"
    merged_context = ""

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 查：看看这个用户以前有没有聊过
            cursor.execute("SELECT history_text FROM user_memory WHERE user_id = %s", (req.user_id,))
            result = cursor.fetchone()
            
            # 2. 拼：拼接记忆
            if result and result.get('history_text'):
                old_history = result['history_text']
                merged_context = f"{old_history}\n{new_message}"
            else:
                merged_context = new_message
                
            # 3. 存：把最新的长记忆覆盖写回数据库
            sql = """
                INSERT INTO user_memory (user_id, history_text) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE history_text = %s
            """
            cursor.execute(sql, (req.user_id, merged_context, merged_context))
        
        conn.commit() # 提交保存
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")
    finally:
        conn.close() # 无论成功失败，必须关门（释放连接）

    # 4. 返：把拼好的长文本发回给低代码平台
    return {
        "status": "success",
        "merged_context": merged_context
    }


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

    # 模拟预测结果（预留真实模型接口位置）
    mock_prediction = sum(req.sales) / len(req.sales) if sales_length > 0 else 0.0
    prediction_result = round(mock_prediction * 1.05, 2) 

    return {
        "status": "success",
        "route_info": {"selected_model": selected_model_name},
        "prediction_result": prediction_result
    }
