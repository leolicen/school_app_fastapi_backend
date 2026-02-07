from httpx import AsyncClient
import logging
import json


logger = logging.getLogger(__name__)




async def test_get_current_student_with_valid_token(async_client: AsyncClient, auth_header):
    
    response = await async_client.get("/students/me", headers=auth_header)
    
    print("\n")
    print("Response model:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("\n")
    
    assert response.status_code == 200
    assert response.json()["surname"] == "Doe"

# without token

async def test_get_current_student_with_invalid_token(async_client: AsyncClient):
    
    response = await async_client.get("/students/me", headers={"Authorization": "Bearer dsvjkbcjcsdkh"})
    
    assert response.status_code == 401
    