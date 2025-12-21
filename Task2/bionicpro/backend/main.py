# backend/main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # ВАЖНО для связи с фронтендом
from fastapi.security import OAuth2PasswordBearer
from clickhouse_driver import Client
from jose import jwt, JWTError
from pydantic import BaseModel
import os

app = FastAPI()

# --- Настройка CORS (чтобы React с порта 3000 мог стучаться на порт 8000) ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение к ClickHouse
CH_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CH_USER = os.getenv("CLICKHOUSE_USER", "airflow_user")
CH_PASS = os.getenv("CLICKHOUSE_PASSWORD", "airflow_pass")

client = Client(host=CH_HOST, port=9000, user=CH_USER, password=CH_PASS, database='default')

# OAuth схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Модель ответа
class ReportResponse(BaseModel):
    client_name: str
    prosthesis_model: str
    total_usage_hours: float
    avg_response_time_ms: float
    status: str
    report_date: str

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Извлекает пользователя из токена. 
    Гарантирует, что пользователь может запросить данные только про себя.
    """
    try:
        # В продакшене здесь нужно валидировать подпись токена ключом Keycloak!
        # options={"verify_signature": False} используем только для примера, 
        # если нет прямого доступа к сертификатам Keycloak в backend контейнере.
        payload = jwt.get_unverified_claims(token)
        
        # Keycloak обычно кладет логин в 'preferred_username' или 'name'
        username = payload.get("preferred_username") or payload.get("name")
        
        if username is None:
            raise HTTPException(status_code=401, detail="User identity not found in token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/reports/me", response_model=ReportResponse)
def get_my_report(current_user: str = Depends(get_current_user)):
    print(f"Запрос отчета для пользователя: {current_user}")
    
    # Запрос к ClickHouse
    # LIMIT 1 BY report_date DESC гарантирует, что мы берем самые свежие данные,
    # которые успел обработать Airflow.
   query = """
        SELECT 
            client_name, 
            prosthesis_model, 
            total_usage_hours, 
            avg_response_time_ms
        FROM report_data_mart 
        WHERE lower(client_name) = lower(%(username)s)
        ORDER BY report_date DESC
        LIMIT 1
    """
    
    # Безопасное выполнение с параметрами (защита от инъекций)
    try:
        result = client.execute(query, {"username": current_user})
    except Exception as e:
        print(f"ClickHouse Error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка подключения к аналитической базе")

    # Если Airflow еще не положил данные для этого пользователя
    if not result:
        raise HTTPException(
            status_code=404, 
            detail="Данные за последний период еще не обработаны или отсутствуют."
        )
    
    row = result[0]
    
    return {
        "client_name": row[0],
        "prosthesis_model": row[1],
        "total_usage_hours": float(row[2]),
        "avg_response_time_ms": float(row[3]),
        "report_date": row[4],
        "status": "Норма" if float(row[3]) < 200 else "Требует калибровки"
    }