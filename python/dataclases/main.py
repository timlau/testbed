from dataclasses import dataclass


@dataclass
class MyData:
    name: str
    id: int


@dataclass
class MoreData(MyData):
    email: str


def main() -> None:
    data = MoreData(name="Tim", id=7, email="tla@somedomain.org")
    data2 = MyData(name="Tom", id=5)
    print(data)
    print(data2)


if __name__ == "__main__":
    main()
