import uuid

from httpx import AsyncClient
import pytest
from sqlmodel import Session

from app.models.student import StudentInDB
from app.services.auth import AuthService
from app.utils.json_printer import print_json_response
from app.models.course import CourseInDB


class TestGetCoursesList:
    """ 
    Tests endpoint GET "/courses/".
    """
    
    async def test_get_courses_success(self, async_client: AsyncClient, test_course: CourseInDB):
        
        response = await async_client.get("/courses/")
        
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        assert data[0]["name"] == test_course.name
        assert "course_id" in data[0]

        print_json_response(json_response=data, response_name="Active courses")



class TestGetStudentCourse:
    
    """ 
    Tests endpoint GET "/courses/me".
    """
    
    # fixture for student registered with non existing course_id => for test_course_not_found only
    @pytest.fixture(name="non_existing_course_user_auth_header")
    async def test_non_existing_course_user_header_fixture(self, session: Session, async_client: AsyncClient):
        
        # create student with random course_id
        user = StudentInDB(
            name="John",
            surname="Doe",
            email="john.doe@gmail.com",
            course_id=str(uuid.uuid4()),
            hashed_password=AuthService.get_password_hash("!#CrediblePasSw0rd")
        )

        session.add(user)
        session.commit()
        session.refresh(user)
        
        # login to retrieve tokens
        response = await async_client.post("/auth/login", data={"username": user.email, "password": "!#CrediblePasSw0rd"})
        
        # extract access token
        access_token = response.json()["access_token"]
        
        # return auth header
        return {"Authorization": f"Bearer {access_token}"}
        
    

    async def test_course_found(self, async_client: AsyncClient, auth_header):

        response = await async_client.get("/courses/me", headers=auth_header)

        data = response.json()

        print_json_response(json_response=data, response_name="Student course")

        assert response.status_code == 200

        assert data["name"] == "Biennio 2023-25 Cyber"

    
    
    async def test_course_not_found(self, async_client: AsyncClient, non_existing_course_user_auth_header):
        
        response = await async_client.get("/courses/me", headers=non_existing_course_user_auth_header)
        
        data = response.json()
        
        assert response.status_code == 404
        
        assert data["error"]["message"] == "Course not found"
    