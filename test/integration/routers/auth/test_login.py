from httpx import AsyncClient
import logging

from app.models.student import StudentInDB


logger = logging.getLogger(__name__)



class TestLoginWithExistingUser:
    """ Test login scenarios for registered users """

    async def test_login_with_valid_credentials(self, async_client: AsyncClient, test_user: StudentInDB):
        
        response = await async_client.post("/auth/login", data={"username": test_user.email, "password": "!#CrediblePasSw0rd"})
        
        assert response.status_code == 200
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        
        
    
    async def test_login_with_invalid_password(self, async_client: AsyncClient, test_user: StudentInDB):
        
        response = await async_client.post("/auth/login", data={"username": test_user.email, "password": "ciao"})
        
        assert response.status_code == 401
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        
        
        
        
    async def test_login_with_no_password(self, async_client: AsyncClient, test_user: StudentInDB):
        
        response = await async_client.post("/auth/login", data={"username": test_user.email, "password": ""})
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.json()}")
        
        # assert Validation Error => raised by Pydantic that validates through OAuth2PasswordRequestForm
        assert response.status_code == 422
        
        
        
    



class TestLoginWithNonExistingUser:
    """ Test login scenarios for non-registered users """
    
    async def test_login_with_no_email(self, async_client: AsyncClient):
        
        response = await async_client.post("/auth/login", data={"username": "", "password": "!#CrediblePasSw0rd"})
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.json()}")
        
        assert response.status_code == 422
        
        
    
    async def test_login_with_non_registered_correct_email(self, async_client: AsyncClient):
        
        response = await async_client.post("/auth/login", data={"username": "testemail@yahoo.com", "password": "!#CrediblePasSw0rd"})
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.json()}")
        
        assert response.status_code == 401
        
        
        
    async def test_login_with_incorrect_email(self, async_client: AsyncClient):
        
        response = await async_client.post("/auth/login", data={"username": "abc", "password": "!#CrediblePasSw0rd"})
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.json()}")
        
        assert response.status_code == 401





      
        
        
        
        

    

