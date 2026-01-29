from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Tuple
from typing import Sequence
import uuid
from sqlalchemy import and_, exists
from sqlmodel import Session, select
from ..models.internship_agreement import InternshipAgreementInDB, InternshipAgreementPublic
from ..models.student import StudentPublic
from ..models.internship_entry import InternshipEntryInDB, InternshipEntryPublic, InternshipEntryCreate
import logging
from ..exceptions.exceptions import (AgreementForbiddenError, InternshipCompletedError, 
                                     InternshipHoursExceededError, InternshipOverlappingEntryError, 
                                     InternshipEntryNotDeletableError)

logger = logging.getLogger(__name__)



class InternshipService():
    
    def __init__(self, session: Session):
        self._db = session
        
    
    # -- GET INTERNSHIP AGREEMENTS -- (a single student can have more than one agreement if they change company)
    def get_internship_agreements_list(self, current_student: StudentPublic) -> List[InternshipAgreementPublic]:
        
        # retrieve agreement/s connected to student id (active & non-active) + company name for each agreement
        get_agreements_stmt = select(
            InternshipAgreementInDB,
            InternshipAgreementInDB.company.name
            ).where(
            InternshipAgreementInDB.student_id == current_student.student_id
        )
        
        # each tuple = (InternshipAgreementInDB, company_name)
        agreements_tuples: Sequence[Tuple[InternshipAgreementInDB, str]] = self._db.exec(get_agreements_stmt).all()
        
        return [InternshipAgreementPublic.model_validate(agr, update={"company_name": name}, from_attributes=True) for agr, name in agreements_tuples]
            
    
    
    
    
    # -- GET OWNED AGREEMENT -- retrieve agreement only if owned 
    def get_owned_agreement(self, student_id: uuid.UUID, agreement_id: uuid.UUID) -> InternshipAgreementPublic | None:
        
        # retrieve agreement only if it belongs to the student
        agreement = self._db.exec(
            select(InternshipAgreementInDB).where(
                InternshipAgreementInDB.student_id == student_id,
                InternshipAgreementInDB.agreement_id == agreement_id
            )
        ).first()

        return InternshipAgreementPublic.model_validate(agreement) if agreement else None
  
    
    
    # -- STUDENT OWNS SPECIFIC ACTIVE AGREEMENT -- 
    def student_owns_specific_active_agreement(self, student_id: uuid.UUID, agreement_id: uuid.UUID) -> bool:
        
        # retrieve owned agreement
        owned_agreement = self.get_owned_agreement(student_id, agreement_id)
        
        # check if owned agreement is active
        return owned_agreement is not None and owned_agreement.is_active
       
    
    
    
    # -- GET INTERNSHIP ENTRIES LIST -- 
    def get_internship_entries_list(self, agreement_id: uuid.UUID) -> List[InternshipEntryPublic]:
        
        # retrieve specific agreement entries in ascending order (from oldest to newest)
        get_entries_stmt = select(InternshipEntryInDB).where(
            InternshipEntryInDB.agreement_id == agreement_id
        ).order_by(InternshipEntryInDB.date.asc())
        
        entries_in_db: Sequence[InternshipEntryInDB] = self._db.exec(get_entries_stmt).all()
        
        
        return [InternshipEntryPublic.model_validate(e) for e in entries_in_db]
    
    
    
    
    # -- GET REMAINING HOURS -- 
    def get_remaining_hours(self, agreement_id: uuid.UUID) -> Decimal:
        
        # retrieve total hours and attended hours from agreement
        result = self._db.exec(select(
            InternshipAgreementInDB.total_hours, 
            InternshipAgreementInDB.attended_hours
            ).where(
            InternshipAgreementInDB.agreement_id == agreement_id
        )
        ).first()
        
        if result is None: # None only if agreement does not exist
            logger.warning(f"Agreement {agreement_id} missing despite ownership check")
            return AgreementForbiddenError()

        
        total_hours, attended_hours = result
        attended_hours = attended_hours or Decimal("0") # in case of None
        
        remaining_hours = total_hours-attended_hours
        
        return remaining_hours
    
    
    
    # -- VALIDATE REMAINING HOURS --
    def validate_remaining_hours(self, agreement_id: uuid.UUID, entry: InternshipEntryCreate) -> None:
        
        # retrieve agreement remaining hours
        remaining_hours: Decimal = self.get_remaining_hours(agreement_id)
              
        # check if internship is already over
        if remaining_hours <= 0:
            logger.warning("Internship completed. Cannot create new entry.")
            raise InternshipCompletedError()
            
        # get total hours to add
        entry_hours = entry.end_time - entry.start_time
        
        # check if entry hours are more than remaining ones
        if entry_hours > remaining_hours:
            logger.warning(f"Student is trying to insert {entry_hours} hours, but only {remaining_hours} are left")
            raise InternshipHoursExceededError(requested=entry_hours, remaining=remaining_hours)



    # -- VALIDATE ENTRY NO OVERLAP --
    def validate_entry_no_overlap(self, agreement_id: uuid.UUID, entry: InternshipEntryCreate) -> InternshipEntryInDB:
        
         # check perfect duplicates with UniqueConstraint in InDB model
        db_entry = InternshipEntryInDB.model_validate(entry)
        
        # check overlapping hours
        # exists() does not instantiate models, but only checks existence
        overlap_stmt = select(exists().where(
            InternshipEntryInDB.agreement_id == agreement_id,
            InternshipEntryInDB.date == db_entry.date,
            and_(
                InternshipEntryInDB.start_time < db_entry.end_time, 
                InternshipEntryInDB.end_time > db_entry.start_time 
            )
        )
        )
        
        # execute query => bool (1 o 0)
        overlap_exists = self._db.exec(overlap_stmt).scalar()
    
        if overlap_exists:
            logger.warning("Overlapping entry time")
            raise InternshipOverlappingEntryError()
        
        return db_entry
    
    
    
    # -- CREATE ENTRY AND UPDATE AGREEMENT --
    def create_entry_and_update_agreement(self, agreement_id: uuid.UUID, valid_entry: InternshipEntryInDB, entry_hours: Decimal) -> InternshipEntryInDB:
        
        with self._db.begin():

            # add db_entry to db
            self._db.add(valid_entry)
            
            # retrieve agreement
            agreement = self._db.get(InternshipAgreementInDB, agreement_id)
            
            # update agreement attended hours
            if agreement:
                current_attended = agreement.attended_hours or Decimal("0")
                updated_attended = current_attended + entry_hours
                agreement.attended_hours = min(updated_attended, agreement.total_hours)
                self._db.add(agreement)
            
            self._db.refresh(valid_entry) 
            
        
        return valid_entry
    

    
    # -- CREATE INTERNSHIP ENTRY -- 
    def create_internship_entry(self, agreement_id: uuid.UUID, entry: InternshipEntryCreate) -> InternshipEntryPublic:
        
        # check if internship is over (remaining hours = 0) or if remaining hours are less than entry ones
        self.validate_remaining_hours(agreement_id, entry)
        
        # check overlapping hours and return EntryInDB
        valid_db_entry: InternshipEntryInDB = self.validate_entry_no_overlap(entry)
        
        # get total entry hours to add 
        entry_hours = entry.end_time - entry.start_time
        
       # add entry to db, update agreement and return EntryInDB
        created_entry: InternshipEntryInDB = self.create_entry_and_update_agreement(agreement_id, valid_db_entry, entry_hours)
        
        
        return InternshipEntryPublic.model_validate(created_entry)
       
        
        
    
    
    
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
            raise InternshipEntryNotDeletableError()
            
        # get total entry hours to subtract
        entry_hours = entry_to_delete.end_time - entry_to_delete.start_time
        
        # get entry agreement id
        agreement_id = entry_to_delete.agreement_id
        
        with self._db.begin():
        
            # delete entry
            self._db.delete(entry_to_delete)
            
            # UPDATE AGREEMENT.ATTENDED_HOURS 
            agreement = self._db.get(InternshipAgreementInDB, agreement_id)
            
            if agreement:
                current_attended = agreement.attended_hours or Decimal("0")
                updated_attended = current_attended - entry_hours
                agreement.attended_hours = max(updated_attended, Decimal("0"))
                self._db.add(agreement)
        

        return {"message": "Entry deleted successfully"}
    
    
    
    # -- GET ENTRY AGREEMENT ID BY ENTRY ID --
    def get_entry_agreement_id_by_entry_id(self, entry_id: uuid.UUID) -> uuid.UUID | None:
        
        agreem_id = self._db.scalar(
            select(InternshipEntryInDB.agreement_id).where(
            InternshipEntryInDB.entry_id == entry_id
        )
        )
    
        return agreem_id
    
    
     
     
     
     
     
        

           
    
     
     
     
     
     
     
     
     
         
  