import pytest
import respx
from consultplace_bot.api.backend import BackendClient


def _add_auth(router: respx.Router) -> None:
    router.post("/auth/token/create/").respond(
        200, json={"access": "dummy", "refresh": "dummy"}
    )
    router.post("/auth/token/refresh/").respond(200, json={"access": "dummy"})

@pytest.fixture(autouse=True, scope="session")
def _force_stub_login():
    BackendClient._patch_login_for_tests()

@pytest.fixture(autouse=True)
def patch_respx(monkeypatch):
    """
    Добавляем моки авторизации и гасим assert_all_called,
    но НЕ трогаем respx.mock – он должен оставаться функцией!
    """
    OrigRouter = respx.router.Router

    class PatchedRouter(OrigRouter):
        def __init__(self, *a, **kw):
            kw.setdefault("assert_all_called", False)
            super().__init__(*a, **kw)
            _add_auth(self)

        # когда тест пишет respx.mock(base_url=...), внутри mock()
        # создаётся Router(...). Нам важно, чтобы и «дочерние»
        # роутеры получали auth-эндпоинты.
        def __call__(self, *a, **kw):          # type: ignore[override]
            sub = super().__call__(*a, **kw)    # обычный Router
            _add_auth(sub)
            return sub

    monkeypatch.setattr(respx.router, "Router", PatchedRouter, raising=True)
    yield

