# ruff: noqa
import pytest
from consultplace_bot.api.backend import BackendClient


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_request_tz_and_estimate(respx_mock):
    cli = BackendClient()
    respx_mock.post("/auth/token/create/").respond(200, json={"access": "a", "refresh": "r"})
    respx_mock.post("/v1/ai/orders/1/tz").respond(200, json={"tz": "Готовое ТЗ", "ai_tz_status": "START"})
    respx_mock.post("/v1/orders/1/estimate").respond(
        200, json={"min_price": 100000, "max_price": 150000, "effort_hours": 80, "currency": "RUB"}
    )
    await cli.login()