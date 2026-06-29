from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import uuid

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, text
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .student import StudentInDB


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


class CourseInDB(CourseBase, table=True):
    # UUID for model id: more secure (unique and unpredictable, does not expose app info)
    course_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Field(index=True) tells SQLModel to create a SQL index for this column
    name: str = Field(max_length=100, index=True, unique=True)

    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=False
        ))

    # inverse relationship: list of enrolled students => only a VIRTUAL relationship, not an actual column
    # 'students' is linked to the 'course' property of Student class
    # allows to access the list of students linked to the course from Course itself
    students: List["StudentInDB"] = Relationship(back_populates="course")


class CourseCreate(CourseBase):
    pass


class CoursePublic(CourseBase):
    course_id: uuid.UUID
    

class CourseUpdate(CourseBase):
    name: Optional[str] = Field(max_length=100, default=None)
    course_type: Optional[str] = Field(max_length=50, default=None)
    schedule: Optional[str] = Field(max_length=100, default=None)
    schedule_type: Optional[str] = Field(max_length=100, default=None)
    total_hours: Optional[int] = Field(gt=0, default=None)
    internship_total_hours: Optional[int] = Field(gt=0, default=None)
    start_date: Optional[date] = Field(default=None)
    location: Optional[str] = Field(max_length=100, default=None)
    is_active: Optional[bool] = Field(default=None)


class CourseListPublic(BaseModel):
    """Model used for public courses list."""
    course_id: uuid.UUID
    name: str = Field(max_length=100)


