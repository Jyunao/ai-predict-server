from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests
import joblib

app = FastAPI()

# 1. 모델 로딩
model = joblib.load("model.pkl")
class_labels = model.classes_.tolist()  # 예: ["HIGH", "LOW", "MEDIUM"]

# 2. 입력 데이터 모델
class WeatherInput(BaseModel):
    location_id: str
    temp: float
    humidity: float
    rain: bool

@app.post("/predict")
def predict(data: WeatherInput):
    try:
        # 3. 입력값 변환
        features = [[data.temp, data.humidity, int(data.rain)]]

        # 4. 예측 및 확률 계산
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        probability_dict = {
            label: round(prob, 4) for label, prob in zip(class_labels, probabilities)
        }

        # 5. 백엔드로 전송할 결과
        result = {
            "location_id": data.location_id,
            "predicted_congestion_level": prediction,
            "prediction_probability": probability_dict,
            "weather": {
                "temp": data.temp,
                "humidity": data.humidity,
                "rain": data.rain
            },
            "predicted_at": datetime.utcnow().isoformat()
        }

        response = requests.post("https://api.jionly.tech/api/congestion", json=result)
        response.raise_for_status()

    except Exception as e:
        return {"status": "error", "message": str(e)}

    # 6. 클라이언트에도 응답
    return {
        "status": "ok",
        "congestion_level": prediction,
        "probabilities": probability_dict
    }
