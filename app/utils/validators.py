import re
from typing import Self


password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'


def strong_password_validator(v: str) -> str:
    if not re.match(password_pattern, v):
        raise ValueError('Password must be at least 8 characters long and contain at least: 1 uppercase letter, 1 lowercase letter, 1 number, 1 special character')
    return v


def passwords_match_validator(self: Self) -> Self:
    if self.new_pwd_confirm != self.new_pwd:
        raise ValueError("New passwords do not match")
    return self


def normalize_email(v: str) -> str:
    if isinstance(v, str):
        return v.lower().strip()
