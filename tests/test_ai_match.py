# tests/test_ai_match.py
import pytest, respx
from consultplace_bot.api.backend import BackendClient

@pytest.mark.asyncio
async def test_match_specialists(respx_mock):
    respx_mock.post("/auth/token/create/").respond(200, json={"access":"a","refresh":"r"})
    respx_mock.post("/v1/ai/orders/1/match").respond(
        200, json={"specialists":[{"id":42,"overall_rating":0.93,"approx_hourly_rate":800}]}
    )

    cli = BackendClient()
    await cli.login()
    items = await cli.match_specialists(1)
    assert items and items[0]["id"] == 42