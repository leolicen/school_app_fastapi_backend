import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, Request

from ..models.internship_agreement import InternshipAgreementPublic
from ..models.student import StudentPublic
from ..dependencies import get_internship_service, get_current_student, get_current_active_student
from ..services.internship import InternshipService
from ..models.internship_entry import InternshipEntryPublic, InternshipEntryCreate
from ..exceptions.exceptions import AgreementForbiddenError, AgreementEntryMismatchError

logger = logging.getLogger(__name__)


# define /internship-agreements router
router = APIRouter(
    prefix="/internship-agreements",
    tags=["internship-agreements"],
)


# protected (active & inactive students)
@router.get("/", response_model=List[InternshipAgreementPublic])
def get_student_agreements(
    current_student: Annotated[StudentPublic, Depends(get_current_student)],
    internship_service: Annotated[InternshipService, Depends(get_internship_service)]
):
    return internship_service.get_internship_agreements_list(current_student)


# protected (active & inactive students)
@router.get("/{agreement_id}/entries", response_model=List[InternshipEntryPublic])
def get_student_agreement_entries(
    request: Request,
    agreement_id: uuid.UUID,
    current_student: Annotated[StudentPublic, Depends(get_current_student)],
    internship_service: Annotated[InternshipService, Depends(get_internship_service)]
):
    # check if agreement belongs to student
    owned_agreement = internship_service.get_owned_agreement(current_student.student_id, agreement_id)

    if owned_agreement is None:
        logger.warning(
            f"Agreement entries access denied at {request.url}",
            extra={
                "student_id": str(current_student.student_id),
                "agreement_id": str(agreement_id),
                "reason": "agreement not owned"
            }
        )
        raise AgreementForbiddenError()

    return internship_service.get_internship_entries_list(agreement_id)


# protected (only active students)
@router.post("/{agreement_id}/entries", response_model=InternshipEntryPublic)
def create_internship_entry(
    request: Request,
    agreement_id: uuid.UUID,
    current_active_student: Annotated[StudentPublic, Depends(get_current_active_student)],
    internship_service: Annotated[InternshipService, Depends(get_internship_service)],
    entry: InternshipEntryCreate
):
    # check if entry belongs to agreement
    if entry.agreement_id != agreement_id:
        raise AgreementEntryMismatchError()

    # check relationship student <-> agreement + active/inactive agreement
    if not internship_service.student_owns_specific_active_agreement(current_active_student.student_id, agreement_id):

        owned_agreement = internship_service.get_owned_agreement(current_active_student.student_id, agreement_id)

        reason = "Agreement not owned" if owned_agreement is None else "Agreement not active"

        logger.warning(
            f"Entry creation denied at {request.url}",
            extra={
                "student_id": str(current_active_student.student_id),
                "agreement_id": str(agreement_id),
                "reason": reason,
                "client_ip": request.client.host
            }
        )
        raise AgreementForbiddenError()

    return internship_service.create_internship_entry(agreement_id, entry)


# protected (only active students)
@router.delete("/{agreement_id}/entries/{entry_id}", response_model=dict[str, str])
def delete_internship_entry(
    request: Request,
    agreement_id: uuid.UUID,
    entry_id: uuid.UUID,
    current_active_student: Annotated[StudentPublic, Depends(get_current_active_student)],
    internship_service: Annotated[InternshipService, Depends(get_internship_service)]
):
    # check relationship student <-> agreement + active/inactive agreement
    if not internship_service.student_owns_specific_active_agreement(current_active_student.student_id, agreement_id):

        owned_agreement = internship_service.get_owned_agreement(current_active_student.student_id, agreement_id)

        reason = "Agreement not owned" if owned_agreement is None else "Agreement not active"

        logger.warning(
            f"Entry deletion denied at {request.url}",
            extra={
                "student_id": str(current_active_student.student_id),
                "agreement_id": str(agreement_id),
                "entry_id": str(entry_id),
                "reason": reason,
                "client_ip": request.client.host
            }
        )
        raise AgreementForbiddenError()

    # extract agreement_id from entry to delete
    entry_agreem_id = internship_service.get_entry_agreement_id_by_entry_id(entry_id)

    if entry_agreem_id is None:
        raise AgreementForbiddenError()

    # check if entry belongs to agreement
    if entry_agreem_id != agreement_id:
        logger.warning("Entry does not belong to this agreement. Cannot delete entry.")
        raise AgreementEntryMismatchError()

    return internship_service.delete_internship_entry(entry_id)
