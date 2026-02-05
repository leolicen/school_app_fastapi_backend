

from fastapi.testclient import TestClient

from app.models.student import StudentInDB


def test_get_current_student_invalid_token(client: TestClient):
    
    response = client.get("/students/me", headers={"Authentication": "Bearer dsvjkbcjcsdkh"})
    
    assert response.status_code == 401
    
    

def test_login_for_access_token(client: TestClient, test_user: StudentInDB):
    
    response = client.post("/auth/login", data={"username": test_user.email, "password": "!#CrediblePasSw0rd"})
    
    assert response.status_code == 200
    
    

def test_get_current_student(client: TestClient, auth_header):
    
    response = client.get("/students/me", headers=auth_header)
    
    assert response.status_code == 200
    assert response.json()["surname"] == "Doe"