import logging

from client import Dnf5DbusClient

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    client = Dnf5DbusClient()
    client.open_session()
    result = client.package_list_fd("dnf5", scope="available", package_attrs=["full_nevra", "changelogs"])
    print(result)
    client.close_session()


if __name__ == "__main__":
    main()
