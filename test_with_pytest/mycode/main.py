from dataclasses import dataclass


@dataclass
class Person:
    name: str = None
    email: str = None

    def __str__(self) -> str:
        return f"My name is {self.name} and my email is {self.email}"

    @classmethod
    def ask_user(cls):
        name = input("What is your name ?")
        email = input("What is your email ?")
        return Person(name=name, email=email)
