from __future__ import annotations

import time
from typing import Optional

import httpx
import respx  # нужен только в _patch_login_for_tests
from pydantic import BaseModel

from consultplace_bot.config import settings


# ------------------------------------------------------------------------------
# Pydantic-модели
# ------------------------------------------------------------------------------
class _TokenPair(BaseModel):
    access: str
    refresh: str


# ------------------------------------------------------------------------------
# HTTP-клиент с auto-refresh JWT
# ------------------------------------------------------------------------------
class _JWTAuth(httpx.Auth):
    """Добавляет Bearer-токен и авто-refresh при 401."""

    requires_request_body = True

    def __init__(self, backend: "BackendClient"):
        self._backend = backend

    async def async_auth_flow(self, request):
        if self._backend.is_expired:
            await self._backend.refresh()

        request.headers["Authorization"] = f"Bearer {self._backend.access}"
        response = yield request

        if response.status_code == 401:
            await self._backend.login()
            request.headers["Authorization"] = f"Bearer {self._backend.access}"
            yield request


class BackendClient:
    """Мини-SDK к CRM/Backend-API."""

    LOGIN_URL = "/auth/token/create/"
    REFRESH_URL = "/auth/token/refresh/"

    # --------------------------------------------------------------------- ctor
    def __init__(self) -> None:
        self._cli: Optional[httpx.AsyncClient] = None
        self._access: Optional[str] = None
        self._refresh: Optional[str] = None
        self._exp_ts: float = 0.0  # unix-время истечения access-токена

    # ----------------------------------------------------------- helpers / misc
    def _get_cli(self) -> httpx.AsyncClient:
        """Создаём AsyncClient лениво — это упрощает мокинг в тестах."""
        if self._cli is None:
            self._cli = httpx.AsyncClient(
                base_url=settings.backend_base_url,
                auth=_JWTAuth(self),
                timeout=20.0,
            )
        return self._cli

    # ----------------------------------------------------------------- props
    @property
    def access(self) -> str:  # noqa: D401
        if self._access is None:
            raise ValueError("Access token is not set (call .login() first)")
        return self._access

    @property
    def is_expired(self) -> bool:
        return self._exp_ts == 0.0 or time.time() > self._exp_ts - 30

    # ----------------------------------------------------------- auth / tokens
    async def login(self) -> None:
        """Логинимся в CRM; access/refresh хранятся в self."""
        resp = await self._get_cli().post(
            self.LOGIN_URL,
            json={"username": settings.backend_user, "password": settings.backend_password},
            auth=None,  # отключаем кастомную _JWTAuth
        )
        resp.raise_for_status()
        self._set_tokens(_TokenPair.model_validate(resp.json()))

    async def refresh(self) -> None:
        """Обновляем access-токен (вызывается авто-хендлером _JWTAuth)."""
        resp = await self._get_cli().post(self.REFRESH_URL, json={"refresh": self._refresh}, auth=None)

        if resp.status_code == 401:  # refresh протух — логинимся заново
            await self.login()
            return

        resp.raise_for_status()
        self._set_tokens(_TokenPair.model_validate(resp.json()))

    # ----------------------------------------------------------------- helpers
    def _set_tokens(self, pair: _TokenPair) -> None:
        self._access = pair.access
        self._refresh = pair.refresh
        self._exp_ts = time.time() + 5 * 60  # access живёт 5 минут

    # -------------------------------------------------------------- API calls
    async def register_user(self, payload: dict) -> int:
        resp = await self._get_cli().post("/api/telegram/register/", json=payload)
        resp.raise_for_status()
        return resp.json()["user_id"]

    async def create_order(self, data: dict) -> int:
        resp = await self._get_cli().post("/orders/", json=data)
        resp.raise_for_status()
        return resp.json()["id"]

    async def request_tz(self, order_id: int, payload: dict) -> str:
        r = await self._get_cli().post(f"/v1/ai/orders/{order_id}/tz", json=payload)
        if r.status_code == 404:
            return "🚧 Генерация ТЗ недоступна (AI-сервис ещё не включён)."
        r.raise_for_status()
        return r.json()["tz"]

    async def estimate_cost(self, order_id: int, tz: str) -> dict:
        r = await self._get_cli().post(f"/v1/orders/{order_id}/estimate", json={"tz": tz})
        r.raise_for_status()
        return r.json()

    async def match_specialists(self, order_id: int, top_n: int = 3) -> list[dict]:
        r = await self._get_cli().post(f"/v1/orders/{order_id}/match", json={"tz": "", "top_n": top_n})
        if r.status_code == 404:
            raise ValueError("AI-match service is not available")
        r.raise_for_status()
        return r.json().get("specialists", [])

    async def list_orders(self, *, mine: bool = True) -> list[dict]:
        r = await self._get_cli().get("/orders/")
        r.raise_for_status()
        return r.json()

    # ----------------------------------------------------------- context-mgr
    async def close(self) -> None:
        if self._cli is not None:
            await self._cli.aclose()
            self._cli = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# «singleton»-экземпляр, чтобы во всём боте использовать один клиент
backend = BackendClient()

# ----------------------------------------------------------------------------------
#  TEST HELPERS
# ----------------------------------------------------------------------------------
@staticmethod
def _patch_login_for_tests() -> None:  # вызывается из tests/conftest.py
    """
    Заменяет метод .login() заглушкой: токены фейковые, а HTTP-вызов
    к /auth/token/create/ делается *только если* он замокан в тесте.
    """
    async def _fake_login(self: "BackendClient") -> None:  # noqa: D401,WPS430
        # ставим валидные «фиктивные» токены
        self._access = "test_access"
        self._refresh = "test_refresh"
        self._exp_ts = time.time() + 3600

        # создаём клиента, если ещё нет
        self._get_cli()

        # пробуем обратиться к /auth/token/create/ — если маршрут
        # замокан (respx), тест увидит вызов; если нет — глотаем ошибку.
        try:
            await self._get_cli().post(self.LOGIN_URL, json={}, auth=None)
        except respx.models.AllMockedAssertionError:  # маршрут не мокнут
            pass

    # просто присваиваем функцию атрибуту класса
    BackendClient.login = _fake_login  # type: ignore[assignment]


# привязываем helper к классу (чтобы вызывался как BackendClient._patch…)
BackendClient._patch_login_for_tests = _patch_login_for_tests  # type: ignore[attr-defined]