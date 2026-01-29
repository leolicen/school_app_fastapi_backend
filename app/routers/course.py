from typing import Annotated
from fastapi import APIRouter, Depends
from ..models.course import CoursePublic
from ..models.student import StudentPublic
from ..dependencies import get_current_student, get_course_service
from ..services.course import CourseService



# define /courses router
router = APIRouter(
    prefix="/courses", 
    tags=["courses"],
)

# -- GET STUDENT COURSE --
# PROTECTED (active & inactive students)
@router.get("/", response_model=CoursePublic)
def get_student_course(
    current_student: Annotated[StudentPublic, Depends(get_current_student)],
    course_service: Annotated[CourseService, Depends(get_course_service)]
    ):
    return course_service.get_student_course(current_student.course_id)