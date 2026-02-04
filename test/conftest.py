import pytest
from fastapi.testclient import TestClient
from sqlalchemy import CheckConstraint
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import app.models
from app.app import app
from app.core.database import get_session



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
        

# -- CLIENT FIXTURE --
@pytest.fixture(name="client")
def client_fixture(session: Session): # session returned by the session fixture
    
    # create override function that returns the test session
    def get_session_override():
        return session

    # override get_session dependency
    app.dependency_overrides[get_session]= get_session_override

    # create a client for our app
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()
    
    
    

