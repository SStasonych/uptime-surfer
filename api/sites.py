from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.site import Site, SiteCheckLog
from schemas.site import SiteCreate, SiteResponse, SiteCheckLogResponse

router = APIRouter(prefix="/sites", tags=["Sites"])
router_logs = APIRouter(prefix="/logs", tags=["Logs"])

# 1: Добавление нового сайта в таблицу 'sites'
@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(site_data: SiteCreate, db: AsyncSession = Depends(get_db)):
    url = str(site_data.url).rstrip("/")
    # 1. Проверяем, нет ли уже такого сайта в базе
    query = select(Site).where(Site.url == url)
    result = await db.execute(query)
    existing_site = result.scalar_one_or_none()

    if existing_site:
        raise HTTPException(
            status_code=400,
            detail="Этот сайт уже добавлен в систему мониторинга"
        )

    new_site = Site(url=url, description=site_data.description)

    db.add(new_site)

    await db.commit()

    # 5. Обновляем объект, чтобы получить его ID, сгенерированный базой
    await db.refresh(new_site)

    return new_site


# 2: Получение списка всех сайтов
@router.get("/", response_model=list[SiteResponse])
async def get_all_sites(db: AsyncSession = Depends(get_db)):
    query = select(Site).order_by(Site.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router_logs.get("/", response_model=list[SiteCheckLogResponse])
async def get_all_logs(db: AsyncSession = Depends(get_db)):
    query = select(SiteCheckLog)
    result = await db.execute(query)
    return result.scalars().all()
