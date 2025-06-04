# # ruff: noqa
# import logging
# import pytest
# import respx
# from consultplace_bot.api.backend import BackendClient
# from consultplace_bot.config import settings
#
# logging.getLogger("aiohttp").setLevel(logging.DEBUG)
# logging.getLogger("httpcore").setLevel(logging.DEBUG)
#
#
#
# @pytest.mark.asyncio
# async def test_login_and_register():
#     client = BackendClient()
#     with respx.mock(base_url=settings.backend_base_url) as router:
#         router.post("/auth/token/create/").respond(200, json={"access": "a", "refresh": "r"})
#         await client.login()
