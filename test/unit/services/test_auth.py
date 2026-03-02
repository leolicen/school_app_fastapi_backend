from datetime import datetime, timedelta, timezone
import uuid

import jwt

from app.core.settings import settings
from app.services.auth import AuthService


class TestGetPasswordHash():
    
    def test_returns_a_string(self):
        result = AuthService.get_password_hash("Secure@123")
        
        assert isinstance(result, str)
    
    
    def test_hash_is_not_plaintext(self):
        password = "Secure@123"
        result = AuthService.get_password_hash(password)
        
        assert result != password
    
    
    def test_same_password_produces_different_hashes(self):
        """ 
        Checks whether Argon2 algorithm generates salt correctly.
        Argon2 uses a casual salt each time, thus producing different
        outputs from the same input.
        """
        
        hash1 = AuthService.get_password_hash("Secure@123")
        hash2 = AuthService.get_password_hash("Secure@123")
        
        assert hash1 != hash2


    def test_hash_is_verifiable(self):
        """ 
        Checks whether the hash created by get_password_hash()
        is verifiable through verify_password().
        """
        
        password = "Secure@123"
        hashed = AuthService.get_password_hash(password)
        
        assert AuthService.verify_password(password, hashed) is True



class TestCreateAccessToken():
    
    def test_returns_a_string(self):
        token = AuthService.create_access_token(id= uuid.uuid4())
        
        assert isinstance(token, str)
    
    
    def test_payload_contains_correct_sub(self):
        student_id = uuid.uuid4()
        token = AuthService.create_access_token(id=student_id)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        assert payload["sub"] == str(student_id)
        

    def test_payload_contains_jti(self):
        token = AuthService.create_access_token(id=uuid.uuid4())
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        assert "jti" in payload
        assert len(payload["jti"]) > 0
        

    def test_default_expiry_is_15_minutes(self):
        before = datetime.now(timezone.utc).replace(microsecond=0)
        token = AuthService.create_access_token(id=uuid.uuid4())
        after = datetime.now(timezone.utc).replace(microsecond=0)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        assert before + timedelta(minutes=15) <= exp <= after + timedelta(minutes=15)


    def test_custom_expiry_is_respected(self):
        delta = timedelta(hours=1)
        before = datetime.now(timezone.utc).replace(microsecond=0)
        token = AuthService.create_access_token(id=uuid.uuid4(), expires_delta=delta)
        after = datetime.now(timezone.utc).replace(microsecond=0)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        assert before + delta <= exp <= after + delta