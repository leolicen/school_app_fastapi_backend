import json
import uuid
from httpx import AsyncClient
import logging

from app.models.course import CourseInDB
from app.models.student import StudentInDB
from app.utils.json_printer import print_json_response

logger = logging.getLogger(__name__)



class TestLoginWithExistingUser:
    """ Test login scenarios for registered users """

    async def test_login_with_valid_credentials(async_client: AsyncClient, test_user: StudentInDB):
        
        response = await async_client.post("/auth/login", data={"username": test_user.email, "password": "!#CrediblePasSw0rd"})
        
        assert response.status_code == 200
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        
        
    
    async def test_login_with_invalid_password(async_client: AsyncClient, test_user: StudentInDB):
        
        response = await async_client.post("/auth/login", data={"username": test_user.email, "password": "ciao"})
        
        assert response.status_code == 401
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        
        
        
        
    async def test_login_with_no_password(async_client: AsyncClient, test_user: StudentInDB):
        
        response = await async_client.post("/auth/login", data={"username": test_user.email, "password": ""})
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.json()}")
        
        # assert Validation Error => raised by Pydantic that validates through OAuth2PasswordRequestForm
        assert response.status_code == 422
        
        
        
    



class TestLoginWithNonExistingUser:
    """ Test login scenarios for non-registered users """
    
    async def test_login_with_no_email(async_client: AsyncClient):
        
        response = await async_client.post("/auth/login", data={"username": "", "password": "!#CrediblePasSw0rd"})
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.json()}")
        
        assert response.status_code == 422
        
        
    
    async def test_login_with_non_registered_correct_email(async_client: AsyncClient):
        
        response = await async_client.post("/auth/login", data={"username": "testemail@yahoo.com", "password": "!#CrediblePasSw0rd"})
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.json()}")
        
        assert response.status_code == 401
        
        
        
    async def test_login_with_incorrect_email(async_client: AsyncClient):
        
        response = await async_client.post("/auth/login", data={"username": "abc", "password": "!#CrediblePasSw0rd"})
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.json()}")
        
        assert response.status_code == 401




class TestRegisterStudent:
    
    async def test_register_success(self, async_client: AsyncClient, test_course: CourseInDB):
        
        # create new student
        new_student = {
            "name": "Paolo",
            "surname": "Rossi",
            "email": "paolo.rossi@gmail.com",
            "course_id": str(test_course.course_id),
            "password": "P@ssW0rd$1cura"
        }
        
        # register new student
        response = await async_client.post("/auth/register", json=new_student)
        
        assert response.status_code == 200
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        
        # create auth header with new student access token
        authorization_header = {"Authorization": f"Bearer {data["access_token"]}"}
        
        # get new student profile
        profile_response = await async_client.get("/students/me", headers=authorization_header)
        
        assert profile_response.status_code == 200
        
        profile = profile_response.json()
        
        print_json_response(json_response=profile, response_name="Newly registered profile")
        
       
        assert profile["email"] == new_student["email"]
        assert profile["name"] == new_student["name"]
        
        
        
        
    async def test_register_with_non_existing_course_id(self, async_client: AsyncClient):
        
        # create new student
        new_student = {
            "name": "Paolo",
            "surname": "Rossi",
            "email": "paolo.rossi@gmail.com",
            "course_id": str(uuid.uuid4()),
            "password": "P@ssW0rd$1cura"
        }
        
        # register new student
        response = await async_client.post("/auth/register", json=new_student)
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert response.status_code == 404
        
        assert "error" in data
        assert "message" in data["error"]
        assert "course" in data["error"]["message"].lower()
        
        
        
        

    

