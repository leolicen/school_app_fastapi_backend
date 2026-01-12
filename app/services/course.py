import uuid
from fastapi import HTTPException, status
from sqlmodel import Session, select
from ..models.course import CourseInDB


class CourseService():
    def __init__(self, session: Session):
        self._db = session
        
    # -- GET STUDENT COURSE --
    def get_student_course(self, course_id: uuid.UUID) -> CourseInDB:
        # seleziono corso in base a id
        get_course_stmt = select(CourseInDB).where(
            CourseInDB.course_id == course_id
        )
        student_course: CourseInDB | None = self._db.exec(get_course_stmt).first()
        
        if not student_course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        return student_course