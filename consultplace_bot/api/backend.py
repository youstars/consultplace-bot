import time
import httpx
from typing import Optional
from pydantic import BaseModel
from consultplace_bot.config import settings


# ---- модели ответов ---------------------------------------------------------
class _TokenPair(BaseModel):
    access: str
    refresh: str


# ---- клиент -----------------------------------------------------------------
class _JWTAuth(httpx.Auth):
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
    LOGIN_URL = "/auth/token/create/"
    REFRESH_URL = "/auth/token/refresh/"

    def __init__(self) -> None:
        self._cli: Optional[httpx.AsyncClient] = None
        self._access: Optional[str] = None
        self._refresh: Optional[str] = None
        self._exp_ts: float = 0.0

    def _get_cli(self) -> httpx.AsyncClient:
        """Lazily create httpx client (helps respx to mock in tests)."""
        if self._cli is None:
            self._cli = httpx.AsyncClient(
                base_url=settings.backend_base_url,
                auth=_JWTAuth(self),
                timeout=20.0,
            )
        return self._cli

    @property
    def access(self) -> str:
        if self._access is None:
            raise ValueError("Access token is not set")
        return self._access

    @property
    def is_expired(self) -> bool:
        if self._exp_ts == 0.0 or self._access is None:
            return True
        return time.time() > self._exp_ts - 30

    async def login(self) -> None:
        """Авторизуется в бэкенде, используя логин и пароль из настроек."""
        client = self._get_cli()
        resp = await client.post(
            self.LOGIN_URL,
            json={"username": settings.backend_user, "password": settings.backend_password},
            auth=None,
        )
        resp.raise_for_status()
        self._set_tokens(_TokenPair.model_validate(resp.json()))

    async def refresh(self) -> None:
        """Обновляет токен доступа, используя refresh-токен."""
        client = self._get_cli()
        resp = await client.post(self.REFRESH_URL, json={"refresh": self._refresh}, auth=None)

        if resp.status_code == 401:
            await self.login()
            return
        resp.raise_for_status()
        tokens = _TokenPair.model_validate(resp.json())
        self._set_tokens(tokens)

    def _set_tokens(self, token: _TokenPair) -> None:
        self._access = token.access
        self._refresh = token.refresh
        self._exp_ts = time.time() + 60 * 5

    async def register_user(self, payload: dict) -> int:
        """Регистрирует нового пользователя и возвращает его ID."""
        resp = await self._get_cli().post("/api/telegram/register/", json=payload)
        resp.raise_for_status()
        return resp.json()["user_id"]

    async def create_order(self, data: dict) -> int:
        """Создаёт новый заказ и возвращает его ID."""
        resp = await self._get_cli().post("/orders/", json=data, auth=None)
        if resp.status_code >= 400:
            print("❌ CRM 400 →", resp.text)
        resp.raise_for_status()
        response_data = resp.json()
        if "id" not in response_data:
            raise ValueError("Order ID not found in response")
        return response_data["id"]

    async def request_tz(self, order_id: int, payload: dict) -> str:
        """Запрашивает техническое задание для заказа."""
        r = await self._get_cli().post(f"/v1/ai/orders/{order_id}/tz", json=payload)
        if r.status_code == 404:
            return "🚧 Генерация ТЗ недоступна (AI-сервис ещё не включён)."
        r.raise_for_status()
        return r.json()["tz"]

    async def estimate_cost(self, order_id: int, tz: str) -> dict:
        """Оценивает стоимость заказа."""
        r = await self._get_cli().post(
            f"/v1/orders/{order_id}/estimate", json={"tz": tz}
        )
        r.raise_for_status()
        return r.json()

    async def match_specialists(self, order_id: int, top_n: int = 3) -> list[dict]:
        """Подбирает специалистов для заказа."""
        r = await self._get_cli().post(
            f"/v1/orders/{order_id}/match", json={"tz": "", "top_n": top_n}
        )
        if r.status_code == 404:
            raise ValueError("AI-match service is not available")
        r.raise_for_status()
        return r.json().get("specialists", [])

    async def list_orders(self, *, mine: bool = True) -> list[dict]:
        """Возвращает список заказов текущего пользователя (или все, если mine=False)."""
        params = {"mine": "1"} if mine else {}
        r = await self._get_cli().get("/orders/", params=params)
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        """Закрывает HTTP-клиент."""
        if self._cli is not None:
            await self._cli.aclose()
            self._cli = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


backend = BackendClient()