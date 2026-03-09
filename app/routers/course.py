from typing import Annotated, List

from fastapi import APIRouter, Depends

from ..models.course import CoursePublic, CourseListPublic
from ..models.student import StudentPublic
from ..dependencies import get_current_student, get_course_service
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


# protected (active & inactive students)
@router.get("/me", response_model=CoursePublic)
def get_student_course(
    current_student: Annotated[StudentPublic, Depends(get_current_student)],
    course_service: Annotated[CourseService, Depends(get_course_service)]
):
    return course_service.get_student_course(current_student.course_id)
