from pydantic import ValidationError
import pytest

from app.models.password import PasswordMatchModel


class TestPasswordMatchModelValid:

    def test_valid_model_returns_correct_fields(self):
        model = PasswordMatchModel(new_pwd="C1@0oooo", new_pwd_confirm="C1@0oooo")

        assert model.new_pwd == "C1@0oooo"
        assert model.new_pwd_confirm == "C1@0oooo"


class TestPasswordMatchModelInvalid:

    def test_passwords_do_not_match(self):
        with pytest.raises(ValidationError, match="New passwords do not match"):
            PasswordMatchModel(new_pwd="C1@0oooo", new_pwd_confirm="C1@ooooo")
