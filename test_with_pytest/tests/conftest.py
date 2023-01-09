import pytest


@pytest.fixture(autouse=True)
def disable_input_calls(monkeypatch):
    def stunted_input():
        raise RuntimeError("User inputs not allowed during testing!")

    monkeypatch.setattr("builtins.input", lambda *args, **kwargs: stunted_input())


@pytest.fixture
def person_data():
    return {"name": "Tim", "email": "tim@somedomain.com"}
