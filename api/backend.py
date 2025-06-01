class BackendClient:
    ...

    async def create_order(self, payload: dict) -> int:
        """Создать заказ и вернуть order_id."""
        resp = await self._cli.post("/orders/", json=payload)
        resp.raise_for_status()
        return resp.json()["order_id"]

    async def request_tz(self, order_id: int, payload: dict) -> str:
        r = await self._cli.post(f"/v1/orders/{order_id}/tz", json=payload)
        r.raise_for_status()
        return r.json()["tz"]

    async def estimate_cost(self, order_id: int, tz: str) -> dict:
        r = await self._cli.post(f"/v1/orders/{order_id}/estimate", json={"tz": tz})
        r.raise_for_status()
        return r.json()