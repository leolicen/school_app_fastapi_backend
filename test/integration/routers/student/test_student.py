from httpx import AsyncClient
import logging

from app.utils.json_printer import print_json_response


logger = logging.getLogger(__name__)




async def test_get_current_student_with_valid_token(async_client: AsyncClient, auth_header):
    
    response = await async_client.get("/students/me", headers=auth_header)
    
    print_json_response(json_response=response.json(), response_name="Current student profile")
    
    assert response.status_code == 200
    assert response.json()["surname"] == "Doe"

# without token

async def test_get_current_student_with_invalid_token(async_client: AsyncClient):
    
    response = await async_client.get("/students/me", headers={"Authorization": "Bearer dsvjkbcjcsdkh"})
    
    assert response.status_code == 401
    