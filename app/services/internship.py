from typing import List
from typing import Sequence
import uuid
from sqlmodel import Session, select
from ..models.internship_agreement import InternshipAgreementInDB, InternshipAgreementPublic
from ..models.student import StudentPublic
from ..models.internship_entry import InternshipEntryInDB, InternshipEntryPublic, InternshipEntryCreate



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
    
    
    # def get_active_agreement(self, current_student: StudentPublic) -> InternshipAgreementPublic:
    #     agreements_list = self.get_internship_agreements_list(current_student)
        
    #     active_agreement = [a for a in agreements_list if a.is_active]
    
    # -- CHECK IF STUDENT OWNS SPECIFIC AGREEMENT --
    def student_owns_specific_agreement(self, student_id: uuid.UUID, agreement_id: uuid.UUID) -> bool:
        # recupero l'agreement specificato solo se appartiene allo studente
        agreement = self._db.exec(
            select(InternshipAgreementInDB).where(
                InternshipAgreementInDB.student_id == student_id,
                InternshipAgreementInDB.agreement_id == agreement_id
            )
        ).first()
        
        # se esiste almeno un agreeement, restituisco True
        return agreement is not None 
    
    
    # -- GET INTERNSHIP ENTRIES LIST --
    def get_internship_entries_list(self, agreement_id: uuid.UUID) -> List[InternshipEntryPublic]:
        # recupero tutte le entry di uno specifico agreement e le ordino dalla più vecchia alla più recente
        get_entries_stmt = select(InternshipEntryInDB).where(
            InternshipEntryInDB.agreement_id == agreement_id
        ).order_by(InternshipEntryInDB.date.asc())
        
        entries_in_db: Sequence[InternshipEntryInDB] = self._db.exec(get_entries_stmt).all()
        
        entries_public_list = [InternshipEntryPublic.model_validate(e) for e in entries_in_db]
        
        return entries_public_list
    
    
    
    # -- CREATE INTERNSHIP ENTRY --
    def create_internship_entry(self, entry: InternshipEntryCreate) -> InternshipEntryPublic:
        
        new_entry = InternshipEntryInDB(
            **entry.model_dump()
        )
        
        self._db.add(new_entry)
        self._db.commit()
        self._db.refresh(new_entry)
        
        return InternshipEntryPublic.model_validate(new_entry)