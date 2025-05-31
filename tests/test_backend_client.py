import pytest, logging, respx
import httpcore
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)

from consultplace_bot.api.backend import BackendClient
from consultplace_bot.config import settings


@pytest.mark.asyncio
async def test_login_and_register():
    client = BackendClient()

    # ↓ контекст-менеджер respx.mock, НЕ Mock
    with respx.mock(base_url=settings.backend_base_url) as router:
        router.post("/api/auth/jwt/create/").respond(
            200, json={"access": "acc", "refresh": "ref"}
        )
        router.post("/api/telegram/register/").respond(
            201, json={"user_id": 42}
        )

        await client.login()
        uid = await client.register_user({"telegram_id": 1, "role": "client"})

        assert uid == 42
        # факультативно: убедиться, что оба маршрута были вызваны
        assert router.calls == 2