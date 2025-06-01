import time, asyncio, httpx
from pydantic import BaseModel
from consultplace_bot.config import settings


# ---- модели ответов ---------------------------------------------------------
class _TokenPair(BaseModel):
    access: str
    refresh: str


# ---- клиент -----------------------------------------------------------------
class _JWTAuth(httpx.Auth):  # базовый класс Auth (sync + async)
    requires_request_body = True

    def __init__(self, backend: "BackendClient"):
        self._backend = backend

    async def async_auth_flow(self, request):
        # авто-refresh перед запросом
        if self._backend.is_expired:
            await self._backend.refresh()

        request.headers["Authorization"] = f"Bearer {self._backend.access}"
        response = yield request  # первый запрос

        # если получили 401 → логинимся заново и ретраим
        if response.status_code == 401:
            await self._backend.login()
            request.headers["Authorization"] = f"Bearer {self._backend.access}"
            yield request  # повторный запрос


class BackendClient:
    LOGIN_URL = "/auth/token/create/"
    REFRESH_URL = "/auth/token/refresh/"

    def __init__(self) -> None:
        self._access = self._refresh = ""
        self._exp_ts: float = 0.0

        self._cli = httpx.AsyncClient(
            base_url=settings.backend_base_url,
            timeout=10,
            auth=_JWTAuth(self),
        )

    # -------- свойства токена ------------
    @property
    def access(self) -> str:
        return self._access

    @property
    def is_expired(self) -> bool:
        return time.time() > self._exp_ts - 30

    # -------- авторизация ----------------
    async def login(self) -> None:
        resp = await self._cli.post(
            self.LOGIN_URL,
            json={"username": settings.backend_user,
                  "password": settings.backend_password},
            auth=None,  # ← не пускаем через _JWTAuth
        )
        resp.raise_for_status()
        self._set_tokens(_TokenPair.model_validate(resp.json()))

    async def refresh(self) -> None:
        resp = await self._cli.post(
            self.REFRESH_URL,
            json={"refresh": self._refresh},
            auth=None,  # ← то же здесь
        )
        if resp.status_code == 401:
            await self.login();
            return
        resp.raise_for_status()
        self._set_tokens(
            _TokenPair(access=resp.json()["access"], refresh=self._refresh)
        )

    def _set_tokens(self, token: _TokenPair) -> None:
        self._access = token.access
        self._refresh = token.refresh
        self._exp_ts = time.time() + 60 * 5  # JWT - 5 минут (пример)

    # -------- бизнес-методы --------------
    async def register_user(self, payload: dict) -> int:
        resp = await self._cli.post("/api/telegram/register/", json=payload)
        resp.raise_for_status()
        return resp.json()["user_id"]

    async def create_order(self, payload: dict) -> int:
        resp = await self._cli.post("/orders/", json=payload)  # или /api/orders/ если нужно
        if resp.status_code >= 400:
            print("❌ CRM 400 →", resp.text)  # ← добавили
        resp.raise_for_status()
        return resp.json().get("id")

    async def request_tz(self, order_id: int, payload: dict) -> str:
        r = await self._cli.post(f"/v1/orders/{order_id}/tz", json=payload)
        r.raise_for_status()
        return r.json()["tz"]

    async def estimate_cost(self, order_id: int, tz: str) -> dict:
        r = await self._cli.post(
            f"/v1/orders/{order_id}/estimate", json={"tz": tz}
        )
        r.raise_for_status()
        return r.json()  # {min_price, max_price, effort_hours, currency}

    # единый инстанс

    async def list_orders(self, *, mine: bool = True) -> list[dict]:
        """Вернуть список заказов текущего пользователя (или все, если mine=False)."""
        params = {"mine": "1"} if mine else {}
        r = await self._cli.get("/orders/", params=params)  # или /api/orders/
        r.raise_for_status()
        return r.json()  # [{id, title, status, ...}, …]


backend = BackendClient()
