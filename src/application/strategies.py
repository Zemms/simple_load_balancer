import re
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from redis import asyncio as aioredis

from src.core.utils import extract_server_name_from_url
from src.domain.enums import ResourceTypeEnum
from src.domain.repositories import BaseCrudRepository, CdnRequestCounterRepository
from src.domain.schemas import TargetResource, CdnServer, OriginServer


class BalancingStrategy(ABC):
    @abstractmethod
    async def get_target_resource(self, video_url: str) -> TargetResource:
        pass


class NthRequestStrategy(BalancingStrategy):
    ORIGIN_HOST_PATTERN = re.compile(r"^(s\d+)\.")

    def __init__(
        self,
        cdn_repo: BaseCrudRepository[CdnServer],
        origin_repo: BaseCrudRepository[OriginServer],
        counter_repo: CdnRequestCounterRepository,
    ):
        self._cdn_repo = cdn_repo
        self._origin_repo = origin_repo
        self._counter_repo = counter_repo

    async def get_target_resource(self, video_url: str) -> TargetResource:
        cdn_settings = await self._cdn_repo.read()

        if cdn_settings is None:
            raise ValueError("Отсутствует установленный CDN")

        try:
            # Получаем данные о сервере (БД или кеш)
            server_name = extract_server_name_from_url(video_url)
            server_settings = await self._origin_repo.read(name=server_name)

            # Каждый N - ный запрос отдаём в оригинальный URL
            counter_value = await self._counter_repo.increment()

            ratio: int = (
                getattr(server_settings, "redirecting_ratio", None)
                or cdn_settings.default_redirecting_ratio
            )

            if not counter_value % ratio:
                return TargetResource(type=ResourceTypeEnum.ORIGIN, url=video_url)

            return TargetResource(
                type=ResourceTypeEnum.CDN,
                url=self._build_cdn_url(video_url, cdn_settings.host_name),
            )

        # Redis свалился - прокидываем через CDN
        except aioredis.RedisError:
            return TargetResource(
                ResourceTypeEnum.CDN,
                url=self._build_cdn_url(video_url, cdn_settings.host_name),
            )

        # Неизвестная ошибка - кидаем оригинальный URL
        except (ValueError, IndexError):
            return TargetResource(type=ResourceTypeEnum.ORIGIN, url=video_url)

    def _build_cdn_url(self, origin_url: str, cdn_host: str) -> str:
        parsed_url = urlparse(origin_url)

        if not parsed_url.hostname:
            raise ValueError("Не смогли получить хост из URL")

        match = self.ORIGIN_HOST_PATTERN.match(parsed_url.hostname)

        if not match:
            raise ValueError(f"Некорректный формат хоста: {parsed_url.hostname}")

        server_name: str = match.group(1)
        video_path = parsed_url.path or ""

        # TODO: Тут бы куда-то вынести префикс http/https
        return f"http://{cdn_host}/{server_name}{video_path}"
