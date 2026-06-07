from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from dataclasses import dataclass
from typing import Any, Self
from urllib.parse import unquote

import httpx

logger = logging.getLogger(__name__)

_UTF8_FILENAME_RE = re.compile(r"filename\*=\s*UTF-8''([^;\s]+)", re.IGNORECASE)
_BASIC_FILENAME_RE = re.compile(r'filename=\s*(?:"([^"]*)"|([^;\s]+))', re.IGNORECASE)

RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})
IDEMPOTENT_METHODS = frozenset({"GET", "PUT", "DELETE", "HEAD", "OPTIONS"})


class HttpClientError(Exception):
    def __init__(self, message: str, url: str, method: str) -> None:
        self.url = url
        self.method = method
        super().__init__(f"{message} [{method} {url}]")


@dataclass(frozen=True)
class File:
    type: str | None
    name: str
    content: bytes


def extract_filename(header: str | None) -> str:
    if header:
        if m := _UTF8_FILENAME_RE.search(header):
            return unquote(m.group(1).replace('"', ""))
        if m := _BASIC_FILENAME_RE.search(header):
            return (m.group(1) or m.group(2) or "").strip()
    return f"download_{int(time.time() * 1000)}"


class HttpClient:
    def __init__(
        self,
        timeout: float = 300.0,
        retries: int = 3,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        keepalive_expiry: float | None = None,
    ) -> None:
        self._retries = retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            transport=httpx.AsyncHTTPTransport(
                http2=True,
                limits=httpx.Limits(
                    max_connections=max_connections,
                    max_keepalive_connections=max_keepalive_connections,
                    keepalive_expiry=keepalive_expiry,
                ),
            ),
            follow_redirects=True,
        )

    @staticmethod
    def _build_headers(
        token: str | None,
        additional_headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        headers: dict[str, str] = dict(additional_headers) if additional_headers else {}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    async def get(
        self,
        url: str,
        token: str | None = None,
        additional_headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        return await self._request_with_backoff(
            method="GET",
            url=url,
            token=token,
            additional_headers=additional_headers,
            params=params,
        )

    async def post(
        self,
        url: str,
        token: str | None = None,
        additional_headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> httpx.Response:
        return await self._request_with_backoff(
            method="POST",
            url=url,
            token=token,
            additional_headers=additional_headers,
            json=json,
            data=data,
        )

    async def put(
        self,
        url: str,
        token: str | None = None,
        additional_headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> httpx.Response:
        return await self._request_with_backoff(
            method="PUT",
            url=url,
            token=token,
            additional_headers=additional_headers,
            json=json,
            data=data,
        )

    async def delete(
        self,
        url: str,
        token: str | None = None,
        additional_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._request_with_backoff(
            method="DELETE", url=url, token=token, additional_headers=additional_headers
        )

    async def download(
        self,
        url: str,
        token: str | None = None,
        additional_headers: dict[str, str] | None = None,
    ) -> File:
        response = await self.get(
            url=url, token=token, additional_headers=additional_headers
        )

        return File(
            type=response.headers.get("content-type"),
            name=extract_filename(response.headers.get("content-disposition")),
            content=response.content,
        )

    async def _request_with_backoff(
        self,
        method: str,
        url: str,
        token: str | None = None,
        additional_headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        is_idempotent = method in IDEMPOTENT_METHODS
        headers = self._build_headers(
            token=token, additional_headers=additional_headers
        )

        for attempt in range(self._retries + 1):
            try:
                response = await self._client.request(
                    method=method, url=url, headers=headers, **kwargs
                )
                response.raise_for_status()
                return response
            except (
                httpx.HTTPStatusError,
                httpx.TimeoutException,
                httpx.NetworkError,
            ) as exc:
                response = getattr(exc, "response", None)
                status_code = (
                    getattr(response, "status_code", None) if response else None
                )

                retryable = is_idempotent and (
                    status_code is None or status_code in RETRYABLE_STATUS_CODES
                )

                if not retryable or attempt == self._retries:
                    raise

            delay = min(0.5 * (2.0**attempt), 30.0) * random.uniform(0.5, 1.0)
            logger.warning(
                "Retrying %s %s in %.1fs (attempt %d)", method, url, delay, attempt + 1
            )
            await asyncio.sleep(delay)

        raise RuntimeError(
            f"Upstream service failed without retry attempt. {method} {url} failed after first attempt."
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
