from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests

app = FastAPI()

class WeatherInput(BaseModel):
    location_id: str
    temp: float
    humidity: float
    rain: bool

@app.post("/predict")
def predict(data: WeatherInput):
    if data.rain:
        level = "HIGH"
    elif data.temp > 30:
        level = "MEDIUM"
    else:
        level = "LOW"

    result = {
        "location_id": data.location_id,
        "predicted_congestion_level": level,
        "weather": {
            "temp": data.temp,
            "humidity": data.humidity,
            "rain": data.rain
        },
        "predicted_at": datetime.utcnow().isoformat()
    }

    try:
        response = requests.post("https://api.jionly.tech/api/congestion", json=result)
        response.raise_for_status()
    except Exception as e:
        return {"error": str(e)}

    return {"status": "ok", "congestion_level": level}
