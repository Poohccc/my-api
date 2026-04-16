from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
fake_database = {}

class StateData(BaseModel):
    user_id: str
    intent: str = ""           # 意图：历史、预测、环比
    keyword: str = ""          # 产品
    history_period: str = ""   # 历史时间
    predict_period: str = ""   # 预测时间

@app.get("/api/get_state")
async def get_state(user_id: str):
    if user_id in fake_database:
        return {"status": "success", "data": fake_database[user_id]}
    return {
        "status": "success",
        "data": {"intent": "", "keyword": "", "history_period": "", "predict_period": ""}
    }

@app.post("/api/save_state")
async def save_state(data: StateData):
    fake_database[data.user_id] = {
        "intent": data.intent, "keyword": data.keyword,
        "history_period": data.history_period, "predict_period": data.predict_period
    }
    return {"status": "success"}
