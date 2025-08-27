import re
from urllib.parse import urlparse

EXTRACT_PATTERN: re.Pattern = re.compile(r"^(s\d+)\.")


def extract_server_name_from_url(video_url: str) -> str | None:
    parsed_url = urlparse(video_url)

    if not parsed_url.hostname:
        raise ValueError("Не смогли получить хост из URL")

    match = EXTRACT_PATTERN.match(parsed_url.hostname)

    if not match:
        raise ValueError(f"Некорректный формат хоста: {parsed_url.hostname}")

    server_name: str = match.group(1)

    return server_name
