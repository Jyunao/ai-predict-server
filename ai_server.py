'''from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests
import joblib

app = FastAPI()

# 모델 로딩
model = joblib.load("congestion_model.pkl")

class WeatherInput(BaseModel):
    location_id: str
    temp: float
    humidity: float
    rain: bool

# 혼잡도 등급 매핑 함수 예시
def categorize_congestion(value):
    if value >= 70:
        return "HIGH"
    elif value >= 40:
        return "MEDIUM"
    else:
        return "LOW"

@app.post("/predict")
def predict(data: WeatherInput):
    # 1. 입력값 구성
    features = [[data.temp, data.humidity, int(data.rain)]]

    # 2. 예측 수행 (수치값)
    try:
        predicted_value = model.predict(features)[0] 
    except Exception as e:
        return {"status": "error", "message": f"예측 실패: {str(e)}"}

    # 3. 등급 분류
    congestion_level = categorize_congestion(predicted_value)

    # 4. 백엔드에 보낼 결과 구성
    result = {
        "location_id": data.location_id,
        "predicted_congestion_level": congestion_level,
        "predicted_congestion_score": round(float(predicted_value), 2), 
        "weather": {
            "temp": data.temp,
            "humidity": data.humidity,
            "rain": data.rain
        },
        "predicted_at": datetime.utcnow().isoformat()
    }

    # 5. 백엔드로 POST
    try:
        response = requests.post("https://api.jionly.tech/api/congestion", json=result)
        response.raise_for_status()
    except Exception as e:
        return {"status": "error", "message": f"백엔드 전송 실패: {str(e)}"}

    # 6. 클라이언트에도 결과 응답
    return {
        "status": "ok",
        "congestion_level": congestion_level,
        "congestion_score": round(float(predicted_value), 2)
    }'''

# ai_server.py 배포 테스트용

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "🚀 FastAPI 서버가 정상적으로 작동 중입니다!"}


