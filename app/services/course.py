import uuid
from sqlmodel import Session, select
from ..models.course import CourseInDB, CoursePublic
import logging
from ..exceptions.exceptions import CourseNotFoundError

logger = logging.getLogger(__name__)


class CourseService():
    def __init__(self, session: Session):
        self._db = session
        
    # -- GET STUDENT COURSE --
    def get_student_course(self, course_id: uuid.UUID) -> CoursePublic:
        
        # select course by id 
        get_course_stmt = select(CourseInDB).where(
            CourseInDB.course_id == course_id
        )
        student_course: CourseInDB | None = self._db.exec(get_course_stmt).first()
        
        if not student_course:
            logger.warning(f"Course {course_id} not found")
            raise CourseNotFoundError()
        
        return CoursePublic.model_validate(student_course)