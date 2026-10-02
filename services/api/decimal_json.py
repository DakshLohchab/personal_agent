"""API request parsing that preserves JSON decimal literals exactly."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from fastapi import Request, Response
from fastapi.routing import APIRoute


class DecimalJSONRequest(Request):
    async def json(self) -> Any:
        if not hasattr(self, "_json"):
            self._json = json.loads(await self.body(), parse_float=Decimal)
        return self._json


class DecimalJSONRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def decimal_json_handler(request: Request) -> Response:
            decimal_request = DecimalJSONRequest(request.scope, request.receive)
            return await original_handler(decimal_request)

        return decimal_json_handler