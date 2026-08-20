import pytest


@pytest.mark.asyncio
async def test_create_and_get_stock(client):
    payload = {"ticker": "infy", "company_name": "Infosys Ltd", "exchange": "NSE", "sector": "IT Services"}

    create_resp = await client.post("/api/v1/stocks", json=payload)
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["ticker"] == "INFY"

    get_resp = await client.get("/api/v1/stocks/INFY")
    assert get_resp.status_code == 200
    assert get_resp.json()["company_name"] == "Infosys Ltd"


@pytest.mark.asyncio
async def test_duplicate_ticker_conflicts(client):
    payload = {"ticker": "TCS", "company_name": "Tata Consultancy Services", "exchange": "NSE"}
    await client.post("/api/v1/stocks", json=payload)
    second = await client.post("/api/v1/stocks", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_unknown_ticker_returns_404(client):
    response = await client.get("/api/v1/stocks/DOESNOTEXIST")
    assert response.status_code == 404
