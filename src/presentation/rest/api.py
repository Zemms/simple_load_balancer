import logging

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import RedirectResponse

from src.application.services import BalancerService
from src.domain.schemas import CdnServer, OriginServer
from .dependencies import (
    get_balancer_service,
    get_cached_origin_repo,
    get_cached_cdn_repo,
    get_origin_persistent_repo,
)
from ...domain.repositories import BaseCrudRepository

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


# Роутер с базовым CRUD для сущности CDN (в единственном числе)
cdn_router = APIRouter(prefix="/cdn")


@cdn_router.get("/")
async def get_cdn_server(
    cdn_repo: BaseCrudRepository[CdnServer] = Depends(get_cached_cdn_repo),
) -> CdnServer | None:
    cdn_server = await cdn_repo.read()

    if cdn_server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cdn server not found",
        )

    return cdn_server


@cdn_router.post("/")
async def create_cdn_server(
    data: CdnServer,
    cdn_repo: BaseCrudRepository[CdnServer] = Depends(get_cached_cdn_repo),
) -> int | None:
    if await cdn_repo.read():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cdn server already exists",
        )

    return await cdn_repo.create(data)


@cdn_router.put("/")
async def update_cdn_server(
    data: CdnServer,
    cdn_repo: BaseCrudRepository[CdnServer] = Depends(get_cached_cdn_repo),
) -> None:
    await cdn_repo.update(id_=None, data=data)


# Роутер с базовым CRUD для сущностей сервера
origin_router = APIRouter(prefix="/origin")


@origin_router.post("/")
async def create_origin_server(
    data: OriginServer,
    origin_repo: BaseCrudRepository[OriginServer] = Depends(get_origin_persistent_repo),
) -> int:
    if await origin_repo.read(name=data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Origin server already exists",
        )

    return await origin_repo.create(data)


@origin_router.put("/")
async def update_origin_server(
    id_: int,
    data: OriginServer,
    origin_repo: BaseCrudRepository[OriginServer] = Depends(get_origin_persistent_repo),
) -> None:
    if await origin_repo.read(name=data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Origin server with same name already exists",
        )

    if await origin_repo.read(id=id_) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origin server not found",
        )

    await origin_repo.update(id_=id_, data=data)


# Добавляем дочерние обработчики в корневой
root_router.include_router(cdn_router)
root_router.include_router(origin_router)
