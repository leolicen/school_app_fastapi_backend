import logging
import uuid
from typing import List, Sequence, Tuple

from sqlmodel import Session, select

from ..models.course import CourseInDB, CoursePublic, CourseListPublic
from ..exceptions.exceptions import CourseNotFoundError

logger = logging.getLogger(__name__)


class CourseService():

    def __init__(self, session: Session):
        self._db = session


    def get_courses_list(self) -> List[CourseListPublic]:
        """Retrieve a list of available courses (active only)."""
        courses_list: Sequence[Tuple[uuid.UUID, str]] = self._db.exec(
            select(CourseInDB.course_id, CourseInDB.name).where(
                CourseInDB.is_active == True
            )
        ).all()

        return [CourseListPublic(course_id=course_id, name=name) for course_id, name in courses_list]


    def get_student_course(self, course_id: uuid.UUID) -> CoursePublic:
        """Retrieve the course attended by the authenticated student."""
        # select course by id
        get_course_stmt = select(CourseInDB).where(
            CourseInDB.course_id == course_id
        )
        student_course: CourseInDB | None = self._db.exec(get_course_stmt).first()

        if not student_course:
            logger.warning(f"Course {course_id} not found")
            raise CourseNotFoundError()

        return CoursePublic.model_validate(student_course)
