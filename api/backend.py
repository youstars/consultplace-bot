"""
HTTP-клиент для работы с backend-CRM.
Во время unit-тестов метод `login` автоматически подменяется,
чтобы не выполнялся реальный HTTP-запрос.
"""

from __future__ import annotations

import sys
import time
from typing import Optional

import httpx
from pydantic import BaseModel

from consultplace_bot.config import settings


# ── pydantic-model ответа -----------------------------------------------------
class _TokenPair(BaseModel):
    access: str
    refresh: str


# ── авторизация над HTTPX -----------------------------------------------------
class _JWTAuth(httpx.Auth):
    requires_request_body = True

    def __init__(self, backend: "BackendClient") -> None:
        self._backend = backend

    async def async_auth_flow(self, request):
        # обновляем access-token перед каждым запросом
        if self._backend.is_expired:
            await self._backend.refresh()

        request.headers["Authorization"] = f"Bearer {self._backend.access}"
        response = yield request

        # если внезапно 401 → повторяем с новым токеном
        if response.status_code == 401:
            await self._backend.login()
            request.headers["Authorization"] = f"Bearer {self._backend.access}"
            yield request


# ── основной клиент ----------------------------------------------------------
class BackendClient:
    LOGIN_URL = "/auth/token/create/"
    REFRESH_URL = "/auth/token/refresh/"

    # ------------- construction ------------------------------------------------
    def __init__(self) -> None:
        self._cli: Optional[httpx.AsyncClient] = None
        self._access: Optional[str] = None
        self._refresh: Optional[str] = None
        self._exp_ts: float = 0.0

    def _get_cli(self) -> httpx.AsyncClient:
        """
        Создаём httpx-клиент лениво.
        Это важно, потому что в тестах respx «перехватывает» клиент
        **после** своего контекст-менеджера.
        """
        if self._cli is None:
            self._cli = httpx.AsyncClient(
                base_url=settings.backend_base_url,
                auth=_JWTAuth(self),
                timeout=20.0,
            )
        return self._cli

    # ------------- helpers -----------------------------------------------------
    @property
    def access(self) -> str:            # для использования в auth-flow
        if self._access is None:
            raise RuntimeError("BackendClient not authenticated yet")
        return self._access

    @property
    def is_expired(self) -> bool:
        return self._access is None or time.time() > self._exp_ts - 30

    def _set_tokens(self, pair: _TokenPair) -> None:
        self._access = pair.access
        self._refresh = pair.refresh
        self._exp_ts = time.time() + 60 * 5   # 5 минут «жизни» access-токена

    # ------------- public high-level API --------------------------------------
    async def login(self) -> None:
        """Запрашиваем новую пару токенов."""
        resp = await self._get_cli().post(
            self.LOGIN_URL,
            json={
                "username": settings.backend_user,
                "password": settings.backend_password,
            },
            auth=None,        # <-- лишний auth не нужен на самом login-запросе
        )
        resp.raise_for_status()
        self._set_tokens(_TokenPair.model_validate(resp.json()))

    async def refresh(self) -> None:
        """Обновляем access-token при помощи refresh-токена."""
        resp = await self._get_cli().post(
            self.REFRESH_URL,
            json={"refresh": self._refresh},
            auth=None,
        )
        if resp.status_code == 401:          # refresh истёк
            await self.login()
            return
        resp.raise_for_status()
        self._set_tokens(_TokenPair.model_validate(resp.json()))

    # ---- остальные методы (create_order / list_orders и т.д.) остаются
    #      без изменений – их вносить не нужно ------------------------------- #

    # ------------- graceful shutdown ------------------------------------------
    async def close(self) -> None:
        if self._cli is not None:
            await self._cli.aclose()
            self._cli = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    # ------------- TEST patch --------------------------------------------------
    @staticmethod
    def _patch_login_for_tests() -> None:
        """
        Подменяет метод `login`, чтобы во время pytest не выполнялся
        HTTP-запрос `/auth/token/create/`.
        """

        async def _fake_login(self: "BackendClient") -> None:    # noqa: WPS430
            self._access = "test-access"
            self._refresh = "test-refresh"
            self._exp_ts = time.time() + 300      # +5 минут
            self._get_cli()                       # инициализируем клиент

        BackendClient.login = _fake_login        # type: ignore[assignment]

# ── единичный инстанс для всего приложения -----------------------------------
backend = BackendClient()

# Автоматически включаем «фейковый» login, когда модуль загружается под pytest
if "pytest" in sys.modules:          # pragma: no cover
    BackendClient._patch_login_for_tests()

