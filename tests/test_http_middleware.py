from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.http_middleware import HttpLoggingMiddleware


def test_http_logging_middleware_passes_mcp_request():
    app = FastAPI()
    app.add_middleware(HttpLoggingMiddleware)

    @app.post("/mcp")
    async def mcp_endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.post("/mcp", json={"jsonrpc": "2.0", "method": "ping"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}