import pytest

from app.utils.validators import strong_password_validator, normalize_email



class TestStrongPasswordValidator:
    
    def test_valid_password(self):
        result = strong_password_validator("Pa$sW0rD!")
        
        assert result == "Pa$sW0rD!"
        
    
    def test_password_too_short(self):
        with pytest.raises(ValueError, match="Password must be at least 8 characters long and contain at least: 1 uppercase letter, 1 lowercase letter, 1 number, 1 special character"):
            strong_password_validator("Pass1!")
            
            
    def test_password_no_uppercase(self):
        with pytest.raises(ValueError):
            strong_password_validator("password!2")
            
            
    def test_password_no_lowercase(self):
        with pytest.raises(ValueError):
            strong_password_validator("PASSWORD!2")
            
            
    def test_password_no_numbers(self):
        with pytest.raises(ValueError):
            strong_password_validator("Password!")
            
            
    def test_password_no_special_chars(self):
        with pytest.raises(ValueError):
            strong_password_validator("Password2")
            



class TestNormalizeEmail:
    
    def test_normalized_email(self):
        normalized_email = normalize_email("Mail@test.com")
        
        assert normalized_email == "mail@test.com"