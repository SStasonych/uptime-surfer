from fastapi import FastAPI
from api.sites import router as sites_router
from api.sites import router_logs as logs_router

app = FastAPI(
    title="Uptime Monitoring API",
    description="Сервис для автоматического мониторинга доступности сайтов",
    version="1.0.0"
)

# Подключаем роутер сайтов к нашему приложению
app.include_router(sites_router, prefix="/api")
app.include_router(logs_router, prefix="/api")

@app.get("/")
def home():
    return {"message": "API работает! Перейдите на /docs для просмотра документации"}
