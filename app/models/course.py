from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import uuid

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, text, event, DDL
from sqlmodel import SQLModel, Field, Relationship

from .guid import GUID

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
    course_id: uuid.UUID = Field(
        sa_column=Column(
            "course_id",
            GUID(),  # sets CHAR(32) as column type, converts CHAR(32) back to Python uuid.UUID
            primary_key=True,
            default=uuid.uuid4  # just in case the record was created Python-side
        )
    )
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


class CoursePublic(CourseBase):
    course_id: uuid.UUID


class CourseListPublic(BaseModel):
    """Model used for public courses list."""
    course_id: uuid.UUID
    name: str = Field(max_length=100)


course_trigger_ddl = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS before_insert_courseindb
    BEFORE INSERT ON courseindb FOR EACH ROW
    BEGIN
        IF NEW.course_id IS NULL OR NEW.course_id = '' THEN
            SET NEW.course_id = REPLACE(UUID(), '-', '');
        END IF;
    END
    """
)


@event.listens_for(CourseInDB.__table__, "after_create")
def create_course_trigger(target, connection, **kw):

    print(f"Tabella: {target.name}")
    print(f"Dialect: {connection.dialect.name}")

    if connection.dialect.name == "mysql":
        connection.execute(course_trigger_ddl)
        result = connection.execute(text("SHOW TRIGGERS LIKE 'before_insert_courseindb'"))
        trigger = result.fetchone()
        print(f"Trigger esiste: {trigger}")
