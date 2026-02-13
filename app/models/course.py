from typing import TYPE_CHECKING, List, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import date, datetime, timezone
import uuid
from sqlalchemy import Boolean, Column, DateTime, text

from .guid import GUID

if TYPE_CHECKING:
    from .student import StudentInDB
    

# -- COURSE BASE --
class CourseBase(SQLModel):
    name: str = Field(max_length=100)
    course_type: str = Field(max_length=50)
    schedule: Optional[str] = Field(max_length=100, default=None)
    schedule_type: Optional[str] = Field(max_length=100, default=None)
    total_hours: int = Field(gt=0)
    internship_total_hours: int = Field(gt=0)
    start_date: date
    location: str = Field(max_length=100)
    is_active: bool = Field(
        default=True,
        sa_column=Column(
            Boolean,
            nullable=False,
            server_default=text("1")
        )
        )


# -- COURSE IN DB --
class CourseInDB(CourseBase, table=True):
    # UUID for models id to guarantee more security (unique and unpredictable id, that does not give info on the app)
    course_id: uuid.UUID = Field(
        sa_column=Column(
            "course_id",
            GUID(), # sets CHAR(32) as column type, converts CHAR(32) back to Python uuid.UUID
            primary_key=True,
            default=uuid.uuid4 # just in case the record was created Python-side
        )
    ) 
    # Field(index=True) tells SQLModel that it should create a SQL index for this column
    name: str = Field(max_length=100, index=True, unique=True)
   
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=False
        ))
    #  Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    # Field(default_factory=lambda: datetime.now(timezone.utc))
     
    # Inverse relationship: list of enrolled students => only a VIRTUAL relationship, not a actual property
    # 'students' property is linked to the 'course' property of Student class
    # allows to access the list of students linked to the course from Course itself
    students: List["StudentInDB"] = Relationship(back_populates="course")


# -- COURSE PUBLIC --
class CoursePublic(CourseBase):
    course_id: uuid.UUID





