from typing import Annotated, List
from fastapi import APIRouter, Depends
from ..models.internship_agreement import InternshipAgreementPublic
from ..models.student import StudentPublic
from ..dependencies import get_internship_service, get_current_student
from ..services.internship import InternshipService


# definisco router /courses 
router = APIRouter(
    prefix="/internships",
    tags=["internships"],
)


# -- GET STUDENT AGREEMENTS --
# endpoint PROTETTO (studenti attivi e inattivi)
@router.get("/agreements", response_model=List[InternshipAgreementPublic])
def get_student_agreements(
    current_student: Annotated[StudentPublic, Depends(get_current_student)],
    internship_service: Annotated[InternshipService, Depends(get_internship_service)]
):
    return internship_service.get_internship_agreements_list(current_student)

