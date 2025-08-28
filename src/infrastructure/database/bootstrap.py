import logging

from sqlalchemy.future import select

from src.infrastructure.database.session import get_async_session
from .models.cdn import CdnServer
from .models.origin import OriginServer

logger = logging.getLogger(__name__)


async def bootstrap_database():
    """
    Тестовый скрипт для заполнения БД начальными данными: один CDN-сервер и несколько
    Origin-серверов. Проверяет наличие данных, чтобы избежать
    дублирования при перезапусках.
    """

    async with get_async_session() as session:
        if await session.scalar(select(CdnServer)):
            return

        # 1 - CDN
        session.add(
            CdnServer(
                host_name="cdn.provider.com",
                default_redirecting_ratio=30
            )
        )

        # 3 - Origin сервера
        session.add_all(
            [
                OriginServer(name="s1.net", redirecting_ratio=20),
                OriginServer(name="s2.net", redirecting_ratio=50),
                OriginServer(name="s3.net", redirecting_ratio=30),
            ]
        )

        await session.commit()
