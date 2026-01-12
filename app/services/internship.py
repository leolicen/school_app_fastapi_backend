from typing import List
from typing import Sequence
from sqlmodel import Session, select
from ..models.internship_agreement import InternshipAgreementInDB, InternshipAgreementPublic
from ..models.student import StudentPublic



class InternshipService():
    def __init__(self, session: Session):
        self._db = session
        
    
    # -- GET INTERNSHIP AGREEMENTS -- (uno studente può avere più di un tirocinio se cambia azienda)
    def get_internship_agreements_list(self, current_student: StudentPublic) -> List[InternshipAgreementPublic]:
        
        # recupero il/gli agreement legati allo student id (includo sia agreement attivi che non)
        get_agreements_stmt = select(InternshipAgreementInDB).where(
            InternshipAgreementInDB.student_id == current_student.student_id
        )
        # recupero Sequence di AgreementInDB
        agreements_in_db: Sequence[InternshipAgreementInDB] = self._db.exec(get_agreements_stmt).all()
        
        # converto in lista di AgreementPublic
        agreements_public_list = [InternshipAgreementPublic.model_validate(agr) for agr in agreements_in_db]
        
        return agreements_public_list
        
        