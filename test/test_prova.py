import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models.student import StudentInDB


@pytest.mark.anyio
async def test_get_current_student_with_valid_token(async_client: AsyncClient, auth_header):
    
    response = await async_client.get("/students/me", headers=auth_header)
    
    assert response.status_code == 200
    assert response.json()["surname"] == "Doe"
    
    


def test_get_current_student_with_invalid_token(client: TestClient):
    
    response = client.get("/students/me", headers={"Authentication": "Bearer dsvjkbcjcsdkh"})
    
    assert response.status_code == 401
    
    

def test_login_with_valid_credentials_and_token(client: TestClient, test_user: StudentInDB):
    
    response = client.post("/auth/login", data={"username": test_user.email, "password": "!#CrediblePasSw0rd"})
    
    assert response.status_code == 200
    
    

