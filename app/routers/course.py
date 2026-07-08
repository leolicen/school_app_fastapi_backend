from typing import Annotated, List

from fastapi import APIRouter, Depends

from ..models.course import CoursePublic, CourseListPublic
from ..models.student import StudentPublic
from ..models.tutor import TutorPublic
from ..models.user import UserRole
from ..dependencies import require_role, get_course_service
from ..services.course import CourseService


# define /courses router
router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)


# public
@router.get("/", response_model=List[CourseListPublic])
def get_courses_list(
    course_service: Annotated[CourseService, Depends(get_course_service)]
):
    return course_service.get_courses_list()


# protected (only tutors)
@router.get("/all", response_model=List[CoursePublic])
def get_full_courses_list(
    current_tutor: Annotated[TutorPublic, Depends(require_role(role=UserRole.TUTOR))],
    course_service: Annotated[CourseService, Depends(get_course_service)]
):
  return course_service.get_full_courses_list()  


# protected (active & inactive students)
@router.get("/me", response_model=CoursePublic)
def get_student_course(
    current_student: Annotated[StudentPublic, Depends(require_role(role=UserRole.STUDENT, active_only=False))],
    course_service: Annotated[CourseService, Depends(get_course_service)]
):
    return course_service.get_student_course(current_student.course_id)


# PATCH "/{COURSE_ID}""

# DELETE "/{COURSE_ID}"