from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List
from typing import Sequence
import uuid
from fastapi import HTTPException, status
from sqlalchemy import and_, exists
from sqlmodel import Session, delete, select, update
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
    
    
  
    
    # -- CHECK IF STUDENT OWNS SPECIFIC AGREEMENT + IF AGREEMENT IS ACTIVE --
    def student_owns_specific_active_agreement(self, student_id: uuid.UUID, agreement_id: uuid.UUID) -> bool:
        # recupero l'agreement specificato solo se appartiene allo studente
        agreement = self._db.exec(
            select(InternshipAgreementInDB).where(
                InternshipAgreementInDB.student_id == student_id,
                InternshipAgreementInDB.agreement_id == agreement_id
            )
        ).first()
        
        if agreement is None or not agreement.is_active:
            return False
        
        
        # se esiste almeno un agreeement attivo, restituisco True
        return True 
    
    
    
    # -- GET INTERNSHIP ENTRIES LIST --
    def get_internship_entries_list(self, agreement_id: uuid.UUID) -> List[InternshipEntryPublic]:
        # recupero tutte le entry di uno specifico agreement e le ordino dalla più vecchia alla più recente
        get_entries_stmt = select(InternshipEntryInDB).where(
            InternshipEntryInDB.agreement_id == agreement_id
        ).order_by(InternshipEntryInDB.date.asc())
        
        entries_in_db: Sequence[InternshipEntryInDB] = self._db.exec(get_entries_stmt).all()
        
        entries_public_list = [InternshipEntryPublic.model_validate(e) for e in entries_in_db]
        
        return entries_public_list
    
    
    def get_remaining_hours(self, agreement_id: uuid.UUID) -> Decimal | None:
        result = self._db.exec(select(
            InternshipAgreementInDB.total_hours, 
            InternshipAgreementInDB.attended_hours
            ).where(
            InternshipAgreementInDB.agreement_id == agreement_id
        )
        ).first()
        
        if not result:
            return None
        
        total_hours, attended_hours = result
        attended_hours = attended_hours or Decimal("0") # in case of None
        
        remaining_hours = total_hours-attended_hours
        
        return remaining_hours

    
    # -- CREATE INTERNSHIP ENTRY --
    def create_internship_entry(self, agreement_id: uuid.UUID, entry: InternshipEntryCreate) -> InternshipEntryPublic:
        
        # retrieve agreement remaining hours
        remaining_hours: Decimal | None = self.get_remaining_hours(agreement_id)
        
        if remaining_hours is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agreement not found"
            )
        # check if internship is already over
        if remaining_hours <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Internship completed. Cannot create new entry."
            )
        # get total hours to add
        entry_hours = entry.end_time - entry.start_time
        # check if entry hours are more than remaining ones
        if entry_hours > remaining_hours:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot insert more than {remaining_hours} hours. Only {remaining_hours} hours left."
            )
        
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
        
        # add db_entry to db
        self._db.add(db_entry)
        
        # UPDATE AGREEMENT.ATTENDED_HOURS 
        agreement = self._db.get(InternshipAgreementInDB, agreement_id)
        if agreement:
            current_attended = agreement.attended_hours or Decimal("0")
            updated_attended = current_attended + entry_hours
            agreement.attended_hours = min(updated_attended, agreement.total_hours)
            self._db.add(agreement)
        
        
        
        self._db.commit()
        self._db.refresh(db_entry)
        
        return InternshipEntryPublic.model_validate(db_entry)
    
    
    
    # -- DELETE INTERNSHIP ENTRY --
    def delete_internship_entry(self, entry_id: uuid.UUID) -> dict[str, str]:
        
        now = datetime.now(timezone.utc)
        
        entry_to_delete = self._db.exec(
            select(InternshipEntryInDB).where(
            InternshipEntryInDB.entry_id == entry_id,
            InternshipEntryInDB.date >= now - timedelta(days=10)
        )
        ).first()
        
        if not entry_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entry not found or too old to be canceled."
            )
        # get total entry hours to subtract
        entry_hours = entry_to_delete.end_time - entry_to_delete.start_time
        # get entry agreement id
        agreement_id = entry_to_delete.agreement_id
        # delete entry
        self._db.delete(entry_to_delete)
        
        # UPDATE AGREEMENT.ATTENDED_HOURS 
        agreement = self._db.get(InternshipAgreementInDB, agreement_id)
        if agreement:
            current_attended = agreement.attended_hours or Decimal("0")
            updated_attended = current_attended - entry_hours
            agreement.attended_hours = max(updated_attended, Decimal("0"))
            self._db.add(agreement)
        
        self._db.commit()
        

       
        return {"message": "Entry deleted successfully"}
    
    
    
    
    def get_entry_agreement_id_by_entry_id(self, entry_id: uuid.UUID) -> uuid.UUID | None:
        agreem_id = self._db.scalar(
            select(InternshipEntryInDB.agreement_id).where(
            InternshipEntryInDB.entry_id == entry_id
        )
        )
    
        return agreem_id
    
    
     