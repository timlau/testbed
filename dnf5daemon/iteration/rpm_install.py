import logging
from pathlib import Path

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
    rpm_path = Path("/home/tim/udv/github/yumex-ng/build/RPMS/noarch/")
    rpm_files: Path = list(rpm_path.glob("*.noarch.rpm"))
    inst_files = [fn.as_posix() for fn in rpm_files]
    print(inst_files)
    client.session_rpm.upgrade(dbus.Array(inst_files), dbus.Dictionary({}))
    res, err = client.resolve()
    # print(list(res))
    for elem in res[0]:
        typ, action, cause, d, pkg = elem
        print(f"type: {typ} action: {action} cause: {cause} nevra: {pkg['full_nevra']} ")
    options = dbus.Dictionary({"comment": "using dnf5daemon for upgrade"})
    client.do_transaction(options)
    problems = list(client.session_goal.get_transaction_problems_string())
    print("tranaction complete")
    for problem in problems:
        print(" --> ", problem)
    client.session_base.reset()
    client.close_session()


if __name__ == "__main__":
    main()
