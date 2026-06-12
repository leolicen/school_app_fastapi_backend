from datetime import date
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import CheckConstraint
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import app.models # only loads models into SQLModel.metadata so that all tables can be created with create_all
from app.app import app
from app.core.database import get_session
from app.models.student import StudentInDB
from app.models.tutor import TutorInDB
from app.services.auth import AuthService
from app.core.redis import get_redis
from app.models.course import CourseInDB



# -- SESSION FIXTURE -- creates a new in-memory db for each and every test
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    for table in SQLModel.metadata.tables.values():
        table.constraints = {c for c in table.constraints if not isinstance(c, CheckConstraint)}
    
    SQLModel.metadata.create_all(engine) # create in-memory db and tables
    
    with Session(engine) as session:
        yield session # return session  
        
        session.rollback()
        

@pytest.fixture(name="mock_redis")
def mock_redis_fixture():
    
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None # simulates access token not blacklisted
    redis_mock.setex.return_value = True # simulates successful token blacklisting 
    redis_mock.aclose.return_value = None # simulates closing of redis client connection (normally returns None)
    
    return redis_mock

        

# -- SYNC CLIENT FIXTURE --
@pytest.fixture(name="client")
def client_fixture(session: Session, mock_redis): # session returned by the session fixture
    
    # create override function that returns the test session
    def get_session_override():
        return session
    
    async def get_redis_override():
        yield mock_redis

    # override get_session dependency
    app.dependency_overrides[get_session]= get_session_override
    # override get_redis dependency
    app.dependency_overrides[get_redis] = get_redis_override

    # create a sync client for our app
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()
    

# -- ASYNC CLIENT FIXTURE -- => for testing endpoints with complex asynchronous logic, calls to async external services, to avoid event loop issues
@pytest.fixture(name="async_client")
async def async_client_fixture(session: Session, mock_redis):
    
    # create override function that returns the test session
    def get_session_override():
        return session
    
    async def get_redis_override():
        yield mock_redis

    # override get_session dependency
    app.dependency_overrides[get_session]= get_session_override
    # override get_redis dependency
    app.dependency_overrides[get_redis] = get_redis_override
    
    # create async client for our app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True
    ) as client:
        yield client
    
    app.dependency_overrides.clear()
    
    
    

# -- TEST STUDENT FIXTURE --
@pytest.fixture(name="test_student")
def test_student_fixture(session: Session, test_course: CourseInDB):
    """ Creates a test student in DB """

    student = StudentInDB(
        name="John",
        surname="Doe",
        email="john.doe@gmail.com",
        course_id=test_course.course_id,
        hashed_password=AuthService.get_password_hash("!#CrediblePasSw0rd")
    )

    session.add(student)
    session.commit()
    session.refresh(student)

    return student



# -- STUDENT ACCESS TOKEN FIXTURE -- => access token string for testing single functions that require token as a string
@pytest.fixture(name="student_access_token")
async def student_access_token_fixture(async_client: AsyncClient, test_student: StudentInDB):
    """ Returns student JWT token string only. Used for functions testing. """
    
    response = await async_client.post("/auth/login", data={"username": test_student.email, "password": "!#CrediblePasSw0rd"})
    
    return response.json()["access_token"]
    
    

# -- STUDENT AUTH HEADER FIXTURE -- => authorization header for endpoint testing only (they require the whole header)
@pytest.fixture(name="student_auth_header")
async def student_auth_header_fixture(student_access_token):
    """ Returns student Authorization header with Bearer token. Used for endpoint testing. """
   
    
    return {"Authorization": f"Bearer {student_access_token}"}



# -- TEST TUTOR FIXTURE --
@pytest.fixture(name="test_tutor")
def test_tutor_fixture(session: Session):
    """ Creates a test tutor in DB """

    tutor = TutorInDB(
        name="Gioacchino",
        surname="Patarnalli",
        email="gio_pata@gmail.com",
        hashed_password=AuthService.get_password_hash("Gr@nd3PATA")
    )

    session.add(tutor)
    session.commit()
    session.refresh(tutor)

    return tutor



# -- TUTOR ACCESS TOKEN FIXTURE -- => access token string for testing single functions that require token as a string
@pytest.fixture(name="tutor_access_token")
async def tutor_access_token_fixture(async_client: AsyncClient, test_tutor: TutorInDB):
    """ Returns tutor JWT token string only. Used for functions testing. """
    
    response = await async_client.post("/auth/login", data={"username": test_tutor.email, "password": "Gr@nd3PATA"})
    
    return response.json()["access_token"]



# -- TUTOR AUTH HEADER FIXTURE -- => authorization header for endpoint testing only (they require the whole header)
@pytest.fixture(name="tutor_auth_header")
async def tutor_auth_header_fixture(tutor_access_token):
    """ Returns tutor Authorization header with Bearer token. Used for endpoint testing. """
   
    
    return {"Authorization": f"Bearer {tutor_access_token}"}



# -- TEST COURSE FIXTURE --
@pytest.fixture(name="test_course")
async def test_course_fixture(session: Session):
    
    course = CourseInDB(
        name="Biennio 2023-25 Cyber",
        course_type="Corso collettivo",
        total_hours=2000,
        internship_total_hours=800,
        start_date=date(2023,11,6),
        location="ITS Umbria Academy.ITS-Scalo Merci"
    )
    
    session.add(course)
    session.commit()
    session.refresh(course)
    
    return course






    
    
    

