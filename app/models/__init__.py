# -- IMPORT "InDB" MODELS -- 
from .auth import ResetTokenInDB, RefreshTokenInDB
from .company import CompanyInDB
from .course import CourseInDB
from .internship_agreement import InternshipAgreementInDB
from .internship_entry import InternshipEntryInDB
from .student import StudentInDB

# __all__ => a list of strings that defines what names should be imported from the current module/package (in this case the models package)
# here used in order to create the "InDB" models before create_all() both in production and test => in conftest.py I declared "import app.models" 
# => in this way all the "InDB" models (tables) get imported and created before the create_all() method is called
# I import only these models because all the others are imported directly by endpoints/services 
__all__ = [
    "ResetTokenInDB",
    "RefreshTokenInDB",
    "CompanyInDB",
    "CourseInDB",
    "InternshipAgreementInDB",
    "InternshipEntryInDB",
    "StudentInDB"
]