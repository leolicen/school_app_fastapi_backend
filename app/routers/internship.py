from typing import Annotated, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from ..models.internship_agreement import InternshipAgreementPublic
from ..models.student import StudentPublic
from ..dependencies import get_internship_service, get_current_student, get_current_active_student
from ..services.internship import InternshipService
from ..models.internship_entry import InternshipEntryPublic, InternshipEntryCreate


# definisco router /courses 
router = APIRouter(
    prefix="/internships-agreements",
    tags=["internships"],
)


# -- GET STUDENT AGREEMENTS --
# endpoint PROTETTO (studenti attivi e inattivi)
@router.get("/", response_model=List[InternshipAgreementPublic])
def get_student_agreements(
    current_student: Annotated[StudentPublic, Depends(get_current_student)],
    internship_service: Annotated[InternshipService, Depends(get_internship_service)]
):
    return internship_service.get_internship_agreements_list(current_student)



# -- GET AGREEMENT ENTRIES --
# endpoint PROTETTO (studenti attivi e inattivi)
@router.get("/{agreement_id}/entries", response_model=List[InternshipEntryPublic])
def get_student_agreement_entries(
    agreement_id: uuid.UUID,
    current_student: Annotated[StudentPublic, Depends(get_current_student)],
    internship_service: Annotated[InternshipService, Depends(get_internship_service)]
    
):
    # controllo che l'agreement appartenga allo studente
    if not internship_service.student_owns_specific_agreement(current_student.student_id, agreement_id):
        raise HTTPException(
            status_code=403,
            detail="Agreement not found or student not authorized"
        )
    
    return internship_service.get_internship_entries_list(agreement_id)


# -- CREATE INTERNSHIP ENTRY --
# endpoint PROTETTO (solo utenti ATTIVI)
@router.post("/{agreement_id}/entries", response_model=InternshipEntryPublic)
def create_internship_entry(
    agreement_id: uuid.UUID,
    current_active_student: Annotated[StudentPublic, Depends(get_current_active_student)],
    internship_service: Annotated[InternshipService, Depends(get_internship_service)],
    entry: InternshipEntryCreate
):
    # check in più su agreement_id
    if entry.agreement_id != agreement_id or not internship_service.student_owns_specific_agreement(current_active_student.student_id, entry.agreement_id):
        raise HTTPException(
            status_code=403,
            detail="Agreement not found or student not authorized. Cannot create entry."
        )
    
    return internship_service.create_internship_entry(entry)



# -- DELETE INTERNSHIP ENTRY --
@router.delete("/{agreement_id}/entries/{entry_id}")
def delete_internship_entry(
    agreement_id: uuid.UUID,
    entry_id: uuid.UUID,
    current_active_student: Annotated[StudentPublic, Depends(get_current_active_student)],
    internship_service: Annotated[InternshipService, Depends(get_internship_service)]
):
    if not internship_service.student_owns_specific_agreement(current_active_student.student_id, agreement_id):
        print(f"Agreement does not match student id.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found. Cannot delete entry."
        )
        
    agreem_id = internship_service.get_entry_agreement_id_by_entry_id(entry_id)
    
    if agreem_id != agreement_id:
        print(f"Agreement does not match entry. Cannot delete entry.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found for this agreement"
        )
        
    
    return internship_service.delete_internship_entry(entry_id)