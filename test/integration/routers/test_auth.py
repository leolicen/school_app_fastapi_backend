from fastapi.testclient import TestClient
import logging

from app.models.student import StudentInDB

logger = logging.getLogger(__name__)


    

def test_login_with_valid_credentials(client: TestClient, test_user: StudentInDB):
    
    response = client.post("/auth/login", data={"username": test_user.email, "password": "!#CrediblePasSw0rd"})
    
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    
  
    
    

