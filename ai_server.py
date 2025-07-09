'''
# 구글 드라이브 연동 X
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


'''
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import os
import joblib
import gdown
import requests
import time

app = FastAPI()

# 모델 파일 경로 & Google Drive 공유 링크
MODEL_PATH = "congestion_model.pkl"
DRIVE_URL = "https://drive.google.com/uc?id=13KwvWuWRXaDVQOU5-TeZMxFYPGE3KJcN" #pkl


# 입력 데이터 모델
class WeatherInput(BaseModel):
    line: str
    station_name: str
    datetime: str
    direction: int #방향 추가
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

# 전역 모델 변수
model = None

@app.post("/predict")
def predict(data: WeatherInput):
    global model

    # 전체 처리 시간 측정 시작
    start_time = time.time()

    # 모델 로딩 (최초 요청 시 1회만 실행)
    if model is None:
        try:
            if not os.path.exists(MODEL_PATH):
                print("모델 파일이 존재하지 않아 Google Drive에서 다운로드를 시도합니다...")
                gdown.download(DRIVE_URL, MODEL_PATH, fuzzy=True)
                print("모델 다운로드 완료.")
            model = joblib.load(MODEL_PATH)
            print("모델 로드 완료.")
        except Exception as e:
            return {"status": "error", "message": f"모델 로드 실패: {e}"}

    # 날짜 파싱 및 파생변수 생성
    try:
        dt = datetime.fromisoformat(data.datetime)
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour
        weekend = int(dt.weekday() >= 5)
        season = ((month % 12 + 3) // 3 - 1)
        Ta = data.TMP
        RH = data.REH / 100
        discomfort = (9/5) * Ta - 0.55 * (1 - RH) * ((9/5) * Ta - 26) + 32
    except Exception as e:
        return {"status": "error", "message": f"날짜 파싱 실패: {e}"}

    # 모델 예측
    try:
        features = [[
            int(data.line), data.TMP, data.VEC, data.WSD,
            data.PCP, data.REH, data.SNO,
            year, month, day, hour,
            discomfort, weekend, season, data.direction
        ]]
        predicted_value = model.predict(features)[0]
    except Exception as e:
        return {"status": "error", "message": f"예측 실패: {e}"}

    level = categorize_congestion(predicted_value)

    result = {
        "line": data.line,
        "station_name": data.station_name,
        "datetime": data.datetime,
        "direction": data.direction,
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

    # 전체 처리 시간 측정 종료
    total_time = round(time.time() - start_time, 3)

    return {
        "status": "ok",
        "congestion_level": level,
        "congestion_score": round(float(predicted_value), 2),
        "total_time_sec": total_time,
        "result": result
    }



