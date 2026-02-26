from typing import List, Sequence, Tuple
import uuid
from sqlmodel import Session, select
from ..models.course import CourseInDB, CoursePublic, CourseListPublic
import logging
from ..exceptions.exceptions import CourseNotFoundError

logger = logging.getLogger(__name__)


class CourseService():
    def __init__(self, session: Session):
        self._db = session
        
        
    # -- GET COURSES LIST --
    def get_courses_list(self) -> List[CourseListPublic]:
        
        courses_list: Sequence[Tuple[uuid.UUID, str]] = self._db.exec(
            select(CourseInDB.course_id, CourseInDB.name)
        ).all()
        
        return [CourseListPublic(course_id=course_id, name=name) for course_id, name in courses_list]
    
    
        
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