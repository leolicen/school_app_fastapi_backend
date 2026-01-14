from datetime import datetime, timedelta, timezone
from typing import List
from typing import Sequence
import uuid
from fastapi import HTTPException, status
from sqlalchemy import and_, exists
from sqlmodel import Session, delete, select
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
        
        # check duplicati perfetti tramite UniqueConstraint nel modello InDB 
        db_entry = InternshipEntryInDB.model_validate(entry)
        
        # check orari turni sovrapposti
        # exists() non istanzia modelli, ma si limita a fare un check di esistenza
        overlap_stmt = select(exists().where(
            InternshipEntryInDB.agreement_id == db_entry.agreement_id,
            InternshipEntryInDB.date == db_entry.date,
            and_(
                InternshipEntryInDB.start_time < db_entry.end_time, 
                InternshipEntryInDB.end_time > db_entry.start_time 
            )
        )
        )
        
        # eseguo query => bool (1 o 0)
        overlap_exists = self._db.exec(overlap_stmt).scalar()
        
        
        if overlap_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Overlapping entry time"
            )
        
        
        self._db.add(db_entry)
        self._db.commit()
        self._db.refresh(db_entry)
        
        return InternshipEntryPublic.model_validate(db_entry)
    
    
    
    # -- DELETE INTERNSHIP ENTRY --
    def delete_internship_entry(self, entry_id: uuid.UUID) -> dict[str, str]:
        now = datetime.now(timezone.utc)
        
        delete_stmt = delete(InternshipEntryInDB).where(
            InternshipEntryInDB.entry_id == entry_id,
            InternshipEntryInDB.date >= now - timedelta(days=10)
        )
        
        result = self._db.exec(delete_stmt)
        deleted_count = result.rowcount
        self._db.commit()
        
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entry not found or too old to be canceled."
            )

       
        return {"message": "Entry deleted successfully"}
    
    
    
    
    def get_entry_agreement_id_by_entry_id(self, entry_id: uuid.UUID) -> uuid.UUID:
        stmt = select(InternshipEntryInDB.agreement_id).where(
            InternshipEntryInDB.entry_id == entry_id
        )
        
        result = self._db.exec(stmt)
        agreem_id = result.first()
        
        if agreem_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entry not found"
            )
        
        return agreem_id
    
    
 