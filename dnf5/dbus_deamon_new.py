import logging
from functools import partial
from timeit import default_timer as timer
from typing import Any, Self

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DBusGMainLoop(set_as_default=True)


DNFDAEMON_BUS_NAME = "org.rpm.dnf.v0"
DNFDAEMON_OBJECT_PATH = "/" + DNFDAEMON_BUS_NAME.replace(".", "/")

IFACE_SESSION_MANAGER = "{}.SessionManager".format(DNFDAEMON_BUS_NAME)
IFACE_REPO = "{}.rpm.Repo".format(DNFDAEMON_BUS_NAME)
IFACE_RPM = "{}.rpm.Rpm".format(DNFDAEMON_BUS_NAME)
IFACE_GOAL = "{}.Goal".format(DNFDAEMON_BUS_NAME)

logger = logging.getLogger("dnf5dbusclient")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
    datefmt="%H:%M:%S",
)


# async call handler class
class AsyncDbusCaller:
    def __init__(self) -> None:
        self.res = None
        self.err = None
        self.loop = None

    def error_handler(self, e) -> None:
        self.err = e
        self.loop.quit()

    def reply_handler(self, r) -> None:
        self.res = r
        self.loop.quit()

    def call(self, mth, *args, **kwargs) -> None | Any:
        self.loop = GLib.MainLoop()
        mth(
            *args,
            **kwargs,
            reply_handler=self.reply_handler,
            error_handler=self.error_handler,
        )
        self.loop.run()
        return self.res, self.err


class Dnf5DBusClient:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.iface_session = dbus.Interface(
            self.bus.get_object(DNFDAEMON_BUS_NAME, DNFDAEMON_OBJECT_PATH),
            dbus_interface=IFACE_SESSION_MANAGER,
        )
        self.async_dbus = AsyncDbusCaller()

    def __enter__(self) -> Self:
        """context manager enter, return current object"""
        # get a session path for the dnf5daemon
        self.open_session()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """context manager exit"""
        self.close_session()
        if exc_type:
            logger.critical("", exc_info=(exc_type, exc_value, exc_traceback))
        # close dnf5 session

    def open_session(self):
        self.session = self.iface_session.open_session({})
        logger.debug(f"open session: {self.session}")
        self.session_repo = dbus.Interface(
            self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
            dbus_interface=IFACE_REPO,
        )
        self.session_rpm = dbus.Interface(
            self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
            dbus_interface=IFACE_RPM,
        )
        self.session_goal = dbus.Interface(
            self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
            dbus_interface=IFACE_GOAL,
        )

    def close_session(self):
        logger.debug(f"close session: {self.session}")
        self.iface_session.close_session(self.session)

    def _async_method(self, method: str, proxy=None) -> partial:
        """create a patial func to make an async call to a given
        dbus method name
        """
        return partial(self.async_dbus.call, getattr(proxy, method))

    def repo_list(self):
        result = self.session_repo.list({"repo_attrs": ["name", "enabled"]})
        # print(result)
        for repo in result:
            print(repo["id"], repo["enabled"])
        return result

    def rpm_list(self, repo):
        get_list = self._async_method("list", self.session_rpm)
        result, err = get_list(
            {
                "package_attrs": ["nevra", "repo_id", "summary"],
                "repo": [repo],
            }
        )

        print(f"repo: {repo} packages: {len(result)}")

        # for i, pkg in enumerate(result[0]):
        #     print(pkg["nevra"])
        #     if i == 10:
        #         break


if __name__ == "__main__":
    with Dnf5DBusClient() as client:
        # get list of available repositories
        repos = client.repo_list()
        # list number of packages in enabled repo
        for repo in repos:
            if repo["enabled"]:
                id = str(repo["id"])
                t1 = timer()
                client.rpm_list(id)
                t2 = timer()
                print(f"execution in {(t2 - t1):.2f}s")
