import logging
import uuid

from httpx import AsyncClient

from app.models.course import CourseInDB
from app.utils.json_printer import print_json_response


logger = logging.getLogger(__name__)



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
        
        
        
    async def test_register_with_empty_password(self, async_client: AsyncClient):
        
        # create new student
        new_student = {
            "name": "Paolo",
            "surname": "Rossi",
            "email": "paolo.rossi@gmail.com",
            "course_id": str(uuid.uuid4()),
            "password": ""
        }
        
        # register new student
        response = await async_client.post("/auth/register", json=new_student)
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert response.status_code == 422
        
    
        


class TestRegisterPasswordValidation:
    
    def setup_student(self, test_course: CourseInDB, password: str):
        base_student = {
                "name": "Paolo",
                "surname": "Rossi",
                "email": "paolo.rossi@gmail.com",
                "course_id": str(test_course.course_id),
                "password": password
            }
        
        return base_student
        
        
    async def test_register_with_short_password(self, async_client: AsyncClient, test_course: CourseInDB):
        """ Test password < 8 chars """
        
        # create new student
        new_student = self.setup_student(test_course=test_course, password="Pass1!")
        
        # register new student
        response = await async_client.post("/auth/register", json=new_student)
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert response.status_code == 422
        
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "detail" in data["error"]
        
        details = data["error"]["detail"]
        
        assert details[0]["loc"] == ["body", "password"]
      
      
        
    async def test_register_with_no_uppercase_password(self, async_client: AsyncClient, test_course: CourseInDB):
        """ Test password with no uppercase """
        
        # create new student
        new_student = self.setup_student(test_course=test_course, password="password!2") 
        
        # register new student
        response = await async_client.post("/auth/register", json=new_student)
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert response.status_code == 422
      
      
      
    async def test_register_with_no_lowercase_password(self, async_client: AsyncClient, test_course: CourseInDB):
        """ Test password with no lowercase """
        
        # create new student
        new_student = self.setup_student(test_course=test_course, password="PASSWORD!2")  
        
        # register new student
        response = await async_client.post("/auth/register", json=new_student)
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert response.status_code == 422
        
        
        
    async def test_register_with_no_numbers_password(self, async_client: AsyncClient, test_course: CourseInDB):
        """ Test password with no numbers """
        
        # create new student
        new_student = self.setup_student(test_course=test_course, password="Password!")  
        
        # register new student
        response = await async_client.post("/auth/register", json=new_student)
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert response.status_code == 422
      
        
        
    async def test_register_with_no_special_chars_password(self, async_client: AsyncClient, test_course: CourseInDB):
        """ Test password with no special chars """
        
        # create new student
        new_student = self.setup_student(test_course=test_course, password="Password2") 
        
        # register new student
        response = await async_client.post("/auth/register", json=new_student)
        
        data = response.json()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {data}")
        
        assert response.status_code == 422