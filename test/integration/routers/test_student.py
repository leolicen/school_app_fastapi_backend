from httpx import AsyncClient
from fastapi.testclient import TestClient



async def test_get_current_student_with_valid_token(async_client: AsyncClient, auth_header):
    
    response = await async_client.get("/students/me", headers=auth_header)
    
    assert response.status_code == 200
    assert response.json()["surname"] == "Doe"

# without token

async def test_get_current_student_with_invalid_token(async_client: AsyncClient):
    
    response = await async_client.get("/students/me", headers={"Authorization": "Bearer dsvjkbcjcsdkh"})
    
    assert response.status_code == 401
    