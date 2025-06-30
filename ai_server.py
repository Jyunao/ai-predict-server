from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests
import joblib

app = FastAPI()

# 모델 로딩 (예측 전 한 번만)
model = joblib.load("congestion_model.pkl")

# 입력 데이터 모델
class WeatherInput(BaseModel):
    line: str
    station_name: str
    station_code: str
    datetime: str
    TMP: float  # 기온
    REH: float  # 습도
    PCP: float  # 강수량
    WSD: float  # 풍속
    SNO: float  # 적설량
    VEC: float  # 풍향

# 혼잡도 등급 분류 함수
def categorize_congestion(value: float) -> str:
    if value <= 80:
        return "여유"
    elif value <= 130:
        return "보통"
    elif value <= 150:
        return "주의"
    else:
        return "혼잡"

@app.post("/predict")
def predict(data: WeatherInput):
    # 입력값 순서 맞추기 (모델 학습에 맞게!)
    features = [[
        data.TMP,
        data.REH,
        data.PCP,
        data.WSD,
        data.SNO,
        data.VEC
    ]]

    try:
        predicted_value = model.predict(features)[0]
    except Exception as e:
        return {"status": "error", "message": f"예측 실패: {str(e)}"}

    level = categorize_congestion(predicted_value)

    result = {
        "line": data.line,
        "station_name": data.station_name,
        "station_code": data.station_code,
        "datetime": data.datetime,
        "TMP": data.TMP,
        "REH": data.REH,
        "PCP": data.PCP,
        "WSD": data.WSD,
        "SNO": data.SNO,
        "VEC": data.VEC,
        "predicted_congestion_score": round(float(predicted_value), 2),
        "predicted_congestion_level": level
    }

    try:
        response = requests.post("https://api.jionly.tech/api/congestion", json=result)
        response.raise_for_status()
    except Exception as e:
        return {"status": "error", "message": f"백엔드 전송 실패: {str(e)}"}

    return {
        "status": "ok",
        "congestion_level": level,
        "congestion_score": round(float(predicted_value), 2)
    }
