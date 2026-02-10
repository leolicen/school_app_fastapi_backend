from datetime import date
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import CheckConstraint
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import AsyncMock
from httpx import ASGITransport, AsyncClient

import app.models # only loads models into SQLModel.metadata so that all tables can be created with create_all
from app.app import app
from app.core.database import get_session
from app.models.student import StudentInDB
from app.services.auth import AuthService
from app.core.redis import get_redis
from app.models.course import CourseInDB



# -- SESSION FIXTURE -- creates a new in-memory db for each and every test
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", # db in-memory
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
        base_url="http://test"
    ) as client:
        yield client
    
    app.dependency_overrides.clear()
    
    
    

# -- TEST USER FIXTURE --
@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """ Creates a test user in DB """
    
    user = StudentInDB(
        name="John",
        surname="Doe",
        email="john.doe@gmail.com",
        course_id=uuid.uuid4(),
        hashed_password=AuthService.get_password_hash("!#CrediblePasSw0rd")
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user



# -- ACCESS TOKEN FIXTURE -- => access token string for testing single functions that require token as a string
@pytest.fixture(name="access_token")
async def access_token_fixture(async_client: AsyncClient, test_user: StudentInDB):
    """ Returns JWT token string only. Used for functions testing. """
    
    response = await async_client.post("/auth/login", data={"username": test_user.email, "password": "!#CrediblePasSw0rd"})
    
    return response.json()["access_token"]
    
    


# -- AUTH HEADER FIXTURE -- => authorization header for endpoint testing only (they require the whole header)
@pytest.fixture(name="auth_header")
async def auth_header_fixture(access_token):
    """ Returns Authorization header with Bearer token. Used for endpoint testing. """
   
    
    return {"Authorization": f"Bearer {access_token}"}



# -- TEST COURSE FIXTURE --
@pytest.fixture(name="test_course")
async def test_course_fixture(session: Session):
    
    course = CourseInDB(
        name="Biennio 2023-25 Cyber",
        course_type="Corso collettivo",
        total_hours=2000,
        internship_total_hours=800,
        start_date=date(2023,11,6),
        location="ITS Umbria Academy.ITS-Scalo Merci",
        course_id=uuid.uuid4()
    )
    
    session.add(course)
    session.commit()
    session.refresh(course)
    
    return course






    
    
    

