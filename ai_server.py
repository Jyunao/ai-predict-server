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
    # 날짜 파싱 및 파생변수 생성
    try:
        dt = datetime.fromisoformat(data.datetime)
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour
        weekend = int(dt.weekday() >= 5)  # 토/일: 1, 평일: 0
        season = ((month % 12 + 3) // 3 - 1)  # 0:봄, 1:여름, 2:가을, 3:겨울
        
        # 불쾌지수 계산 (섭씨 기온 사용)
        Ta = data.TMP
        RH = data.REH / 100  # 0~1로 변환
        discomfort = (9 / 5) * Ta - 0.55 * (1 - RH) * ((9 / 5) * Ta - 26) + 32
        
    except Exception as e:
        return {"status": "error", "message": f"날짜 파싱 실패: {str(e)}"}

    # 입력 피처 순서 (모델 학습 기준과 맞춰야함)
    try:
        features = [[
            int(data.line),         # line
            data.TMP,               # temperature
            data.VEC,               # wind_direction
            data.WSD,               # wind_speed
            data.PCP,               # hourly_precipitation
            data.REH,               # humidity
            data.SNO,               # snow
            year, month, day, hour, # time features
            discomfort,
            weekend,
            season
        ]]

        predicted_value = model.predict(features)[0]
    except Exception as e:
        return {"status": "error", "message": f"예측 실패: {str(e)}"}

    level = categorize_congestion(predicted_value)

    result = {
        "line": data.line,
        "station_name": data.station_name,
        "datetime": data.datetime,
        "TMP": data.TMP,
        "REH": data.REH,
        "PCP": data.PCP,
        "WSD": data.WSD,
        "SNO": data.SNO,
        "VEC": data.VEC,
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "season": season,
        "weekend": weekend,
        "discomfort": round(discomfort, 2),
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
