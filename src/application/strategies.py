import re
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from redis import asyncio as aioredis

from src.domain.enums import ResourceTypeEnum
from src.domain.repositories import CdnSettingsRepository, CdnRequestCounterRepository
from src.domain.schemas import TargetResource


class BalancingStrategy(ABC):
    @abstractmethod
    async def get_target_resource(self, video_url: str) -> TargetResource:
        pass


class NthRequestStrategy(BalancingStrategy):
    ORIGIN_HOST_PATTERN = re.compile(r"^(s\d+)\.")

    def __init__(
        self,
        settings_repo: CdnSettingsRepository,
        counter_repo: CdnRequestCounterRepository,
    ):
        self._settings_repo = settings_repo
        self._counter_repo = counter_repo

    async def get_target_resource(self, video_url: str) -> TargetResource:
        settings = await self._settings_repo.read()

        try:
            counter_value: int = await self._counter_repo.increment()

            # Каждый N - ный запрос отдаём в оригинальный URL
            if not counter_value % settings.ratio:
                return TargetResource(type=ResourceTypeEnum.ORIGIN, url=video_url)

            return TargetResource(
                type=ResourceTypeEnum.CDN,
                url=self._build_cdn_url(video_url, settings.host),
            )

        # Redis оказался недоступен - прокидываем через CDN
        except aioredis.RedisError:
            return TargetResource(
                ResourceTypeEnum.CDN,
                url=self._build_cdn_url(video_url, settings.host),
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
