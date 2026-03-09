from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, DateTime, text, event, DDL

from .guid import GUID


if TYPE_CHECKING:
    from .internship_agreement import InternshipAgreementInDB


class CompanyInDB(SQLModel, table=True):
    """
    Model that simulates a real-world data management scenario by a admin/tutor.
    It also allows to retrieve the company name from InternshipAgreement table with a 'join' query.
    """
    company_id: uuid.UUID = Field(
        sa_column=Column(
            "company_id",
            GUID(),  # sets CHAR(32) as column type, converts CHAR(32) back to Python uuid.UUID
            primary_key=True,
            default=uuid.uuid4  # just in case the record was created Python-side (e.g. during TESTS)
        )
    )
    name: str = Field(max_length=50, unique=True, index=True)
    city: str = Field(max_length=50, index=True)
    address: str = Field(max_length=50)
    tutor: Optional[str] = Field(max_length=40, default=None)

    # creation date & time for log/audit
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=False
        )
    )

    # relationships
    internship_agreements: List["InternshipAgreementInDB"] = Relationship(back_populates="company")


company_trigger_ddl = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS before_insert_companyindb
    BEFORE INSERT ON companyindb FOR EACH ROW
    BEGIN
        IF NEW.company_id IS NULL OR NEW.company_id = '' THEN
            SET NEW.company_id = REPLACE(UUID(), '-', '');
        END IF;
    END
    """
)


@event.listens_for(CompanyInDB.__table__, "after_create")
def create_company_trigger(target, connection, **kw):

    print(f"Tabella: {target.name}")
    print(f"Dialect: {connection.dialect.name}")

    if connection.dialect.name == "mysql":
        connection.execute(company_trigger_ddl)
