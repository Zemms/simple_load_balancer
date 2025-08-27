import logging

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import AnyUrl

from src.application.services import BalancerService
from src.domain.repositories import CdnSettingsRepository
from src.domain.schemas import CdnSettings
from .dependencies import get_balancer_service, get_cached_settings_repo

logger = logging.getLogger(__name__)

# Корневой роутер для основного функционала
root_router = APIRouter()


@root_router.get("/")
async def balance_request(
    video_url: str = Query(description="URL видео-файла на origin сервере"),
    balancer_service: BalancerService = Depends(get_balancer_service),
):
    try:
        redirect_address = await balancer_service.get_redirect_address(video_url)
        return RedirectResponse(
            url=redirect_address.url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )

    # Некорректное значение
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Неизвестная ошибка
    except Exception as e:
        logger.exception(e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error: %s" % str(e),
        )


# Роутер для настроек соответствий
settings_router = APIRouter(prefix="/settings")


@settings_router.post("/")
async def create_settings(
    data: CdnSettings,
    settings_repo: CdnSettingsRepository = Depends(get_cached_settings_repo),
):
    if await settings_repo.read():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Settings already exists",
        )

    await settings_repo.create(data)


@settings_router.get("/")
async def get_settings(
    settings_repo: CdnSettingsRepository = Depends(get_cached_settings_repo),
) -> CdnSettings:
    settings = await settings_repo.read()

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found",
        )

    return settings


@settings_router.put("/")
async def update_settings(
    data: CdnSettings,
    settings_repo: CdnSettingsRepository = Depends(get_cached_settings_repo),
) -> None:
    if await settings_repo.read() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found",
        )

    return await settings_repo.update(data)


root_router.include_router(settings_router)
