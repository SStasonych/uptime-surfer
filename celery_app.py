import asyncio
from datetime import datetime, timezone

import httpx
from celery import Celery
from sqlalchemy import select

# Предполагаем, что в database.py у вас есть асинхронная фабрика сессий
from database import async_session_factory
from models.site import Site, SiteCheckLog

celery_app = Celery(
    "uptime_monitor",
    broker="redis://localhost:6379/0",
    # backend="redis://localhost:6379/0",
)

# Настройка периодического расписания
celery_app.conf.beat_schedule = {
    "check-all-sites-every-minute": {
        "task": "celery_app.check_all_sites",
        "schedule": 60.0,  # каждые 60 секунд
    },
}


@celery_app.task
def check_all_sites():
    asyncio.run(_check_all_sites_async())


async def _check_all_sites_async():
    async with async_session_factory() as db:
        result = await db.execute(select(Site))
        sites = result.scalars().all()

        for site in sites:
            await _check_site_and_log(db, site)


async def _check_site_and_log(db, site):
    start_time = datetime.now()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(site.url)
            status_code = response.status_code
            is_available = 200 <= status_code < 400
    except httpx.HTTPError:
        status_code = 0
        is_available = False

    response_time = (datetime.now() - start_time).total_seconds()

    log_entry = SiteCheckLog(
        site_id=site.id,
        status_code=status_code,
        is_available=is_available,
        response_time=response_time,
        checked_at=datetime.now(),
    )

    db.add(log_entry)
    await db.commit()
