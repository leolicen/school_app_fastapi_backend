import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import CheckConstraint
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import AsyncMock

import app.models # only loads models into SQLModel.metadata so that all tables can be created with create_all
from app.app import app
from app.core.database import get_session
from app.models.student import StudentInDB
from app.services.auth import AuthService
from app.core.redis import get_redis



# -- SESSION FIXTURE --
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
        

@pytest.fixture(name="mock_redis")
def mock_redis_fixture():
    
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None # access token not blacklisted
    redis_mock.setex.return_value = True
    redis_mock.aclose.return_value = None
    
    return redis_mock

        

# -- CLIENT FIXTURE --
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

    # create a client for our app
    client = TestClient(app)
    
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


@pytest.fixture(name="auth_header")
def auth_header_fixture(client: TestClient, test_user: StudentInDB):
    
    response = client.post("/auth/login", data={"username": test_user.email, "password": "!#CrediblePasSw0rd"})
    
    access_token = response.json()["access_token"]
    token_type = response.json()["token_type"]
    
    return {"Authorization": f"{token_type} {access_token}"}



    
    
    

