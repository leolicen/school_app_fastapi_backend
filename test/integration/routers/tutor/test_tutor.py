import logging

from httpx import AsyncClient

from app.utils.json_printer import print_json_response


logger = logging.getLogger(__name__)




async def test_get_current_tutor_with_valid_token(async_client: AsyncClient, tutor_auth_header):
    
    response = await async_client.get("/tutors/me", headers=tutor_auth_header)
    
    print_json_response(json_response=response.json(), response_name="Current tutor profile")
    
    assert response.status_code == 200
    assert response.json()["surname"] == "Patarnalli"

# without token

async def test_get_current_tutor_with_invalid_token(async_client: AsyncClient):
    
    response = await async_client.get("/tutors/me", headers={"Authorization": "Bearer dsvjkbcjcsdkh"})
    
    assert response.status_code == 401
    

async def test_get_current_tutor_by_student(async_client: AsyncClient, student_auth_header):
    
    response = await async_client.get("/tutors/me", headers=student_auth_header)
    
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "You do not have permission to access this resource"
    