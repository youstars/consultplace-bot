import pytest
import respx


from consultplace_bot.api.backend import BackendClient



@pytest.mark.asyncio
async def test_full_backend_happy_path(respx_mock: respx.MockRouter):
    respx_mock.post("/auth/token/create/").respond(200, json={"access": "a", "refresh": "r"})
    respx_mock.post("/orders/").respond(201, json={"id": 1})
    respx_mock.post("/v1/ai/orders/1/tz").respond(200, json={"tz": "ТЗ", "ai_tz_status": "START"})
    respx_mock.post("/v1/orders/1/estimate").respond(
        200, json={"min_price": 10_000, "max_price": 20_000, "effort_hours": 80, "currency": "RUB"}
    )
    respx_mock.post("/v1/orders/1/match").respond(
        200, json={"specialists": [{"id": 42, "overall_rating": 0.95, "approx_hourly_rate": 800}]}
    )
    respx_mock.get("/orders/").respond(
        200, json=[{"id": 1, "status": "NEW", "order_goal": "Сайт под ключ"}]
    )
    async with BackendClient() as cli:
        await cli.login()