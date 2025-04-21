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
    client = Dnf5DbusClient()
    client.open_session()
    updates = [pkg["nevra"] for pkg in client.package_list_fd("*", scope="upgrades")]
    logger.info(f"Number of updates packages : {len(updates)}")
    print(updates[1])
    client.session_rpm.upgrade(dbus.Array(updates), dbus.Dictionary({}))
    res, err = client.resolve()
    # print(list(res))
    for elem in res[0]:
        typ, action, cause, d, pkg = elem
        print(f"type: {typ} action: {action} cause: {cause} nevra: {pkg['full_nevra']} ")
    options = dbus.Dictionary({"comment": "using dnf5daemon for upgrade", "offline": True})
    client.do_transaction(options)
    problems = list(client.session_goal.get_transaction_problems_string())
    print("tranaction complete")
    for problem in problems:
        print(" --> ", problem)
    success, err = client.offline_reboot()
    if success:
        print("Reboot successful")
    else:
        print("Reboot failed")
        print(err)
    client.session_base.reset()
    client.close_session()


if __name__ == "__main__":
    main()
