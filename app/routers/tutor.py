from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from ..models.tutor import TutorPublic, TutorUpdate
from ..models.user import UserRole
from ..models.password import ChangePassword
from ..dependencies import require_role, get_tutor_service, oauth2_scheme
from ..services.tutor import TutorService
from ..core.rate_limiting import limiter


# define /tutor router
router = APIRouter(
    prefix="/tutors",
    tags=["tutors"],
)

# protected
# ANY TUTOR (active & inactive) => anybody can read their own info
@router.get("/me", response_model=TutorPublic)
def get_current_tutor(current_tutor: Annotated[TutorPublic, Depends(require_role(role=UserRole.TUTOR, active_only=False))]):
    return current_tutor


# protected
# tutor must be active to modify data
@router.patch("/me", response_model=TutorPublic)
def update_tutor(
    current_tutor: Annotated[TutorPublic, Depends(require_role(role=UserRole.TUTOR))],
    tutor_service: Annotated[TutorService, Depends(get_tutor_service)],
    tutor_to_update: TutorUpdate
):
    return tutor_service.update_tutor(current_tutor.tutor_id, tutor_to_update)


# protected
# ANY TUTOR can delete their account
@router.delete("/me", response_model=dict[str, str])
async def delete_account(
    current_tutor: Annotated[TutorPublic, Depends(require_role(role=UserRole.TUTOR, active_only=False))],
    tutor_service: Annotated[TutorService, Depends(get_tutor_service)],
    access_token: Annotated[str, Depends(oauth2_scheme)]
):
    return await tutor_service.delete_tutor(current_tutor, access_token)


# protected (within the app => tutor account)
# ANY TUTOR (active & inactive) => anybody can modify their password
@router.post("/change-password", status_code=status.HTTP_200_OK, response_model=dict[str, str])
@limiter.limit("5/15minute")
def change_password(
    request: Request,
    current_tutor: Annotated[TutorPublic, Depends(require_role(role=UserRole.TUTOR, active_only=False))],
    tutor_service: Annotated[TutorService, Depends(get_tutor_service)],
    pwd_data: ChangePassword
):
    tutor_service.change_password(current_tutor, pwd_data)

    return {"detail": "Password updated successfully"}