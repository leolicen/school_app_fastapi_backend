import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

# -- BACKEND-AGNOSTIC GUID TYPE --
class GUID(TypeDecorator):
    """ Platform independent GUID type.
    
    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    
    [https://docs-sqlalchemy.readthedocs.io/ko/latest/core/custom_types.html#backend-agnostic-guid-type]
    
    """
    
    impl = CHAR # default type to be used
    
    cache_ok = True # tells SQLAlchemy this type can be safely cached
    
    # determines which db type to use according to the db dialect
    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))
    
    # Python value --> db value
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID): # if value is a string, converts it to uuid, then int, then formats as 32 hex chars
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int # if value is uuid, converts it to 32 hex chars
            
    # db value --> Python value
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value) 