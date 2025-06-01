import pytest, respx
from consultplace_bot.api.backend import BackendClient

@pytest.mark.asyncio
async def test_list_orders(respx_mock):
    respx_mock.post("/auth/token/create/").respond(200, json={"access":"a","refresh":"r"})
    respx_mock.get("/orders/").respond(200, json=[{"id":1,"status":"NEW","order_goal":"Тест"}])

    cli = BackendClient()
    await cli.login()
    items = await cli.list_orders()
    assert items[0]["id"] == 1