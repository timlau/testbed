import logging

import dbus
from client import Dnf5DbusClient

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    number_interation = 10
    client = Dnf5DbusClient()
    client.open_session()
    for i in range(number_interation):
        print(f"Interation : {i + 1}")
        installed = list(client.package_list_fd("*", package_attrs=["full_nevra"], scope="installed"))
        logger.info(f"Number of installed packages : {len(installed)}")
        pkg = client.package_list_fd("0xffff")[0]
        nevra = pkg["nevra"]
        logger.info(f"--> Installing {nevra}")
        logger.debug(f"DBUS: {client.session_rpm.object_path}.install()")
        client.session_goal.reset()
        client.session_rpm.install(dbus.Array([nevra]), dbus.Dictionary({}))
        res, err = client.resolve()
        print(list(res))
        rc = client.do_transaction()
        logger.info(f"tranaction complete (rc={rc})")
        client.session_base.reset()
        installed = list(client.package_list_fd("*", package_attrs=["full_nevra"], scope="installed"))
        logger.info(f"Number of installed packages : {len(installed)}")
        pkg = client.package_list_fd("0xffff")[0]
        nevra = pkg["nevra"]
        logger.info(f"--> Removing {nevra}")
        logger.debug(f"DBUS: {client.session_rpm.object_path}.install()")
        client.session_goal.reset()
        client.session_rpm.remove(dbus.Array([nevra]), dbus.Dictionary({}))
        rc = client.resolve()
        rc = client.do_transaction()
        logger.info(f"tranaction complete (rc={rc})")
        client.session_base.reset()
    client.close_session()


if __name__ == "__main__":
    main()
