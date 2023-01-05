from functools import partial
from importlib.resources import path
from logging import getLogger
from typing import Self
from dasbus.connection import SystemMessageBus
from dasbus.error import DBusError, ErrorMapper, get_error_decorator
from dasbus.identifier import DBusServiceIdentifier
from dasbus.loop import EventLoop
import traceback
from gi.repository import GLib

# Constants
SYSTEM_BUS = SystemMessageBus()
# org.rpm.dnf.v0.Goal
# org.rpm.dnf.v0.SessionManager
# org.rpm.dnf.v0.rpm.Repo
# org.rpm.dnf.v0.rpm.Rpm
DNFDBUS_NAMESPACE = ("org", "rpm", "dnf", "v0")
DNFDBUS = DBusServiceIdentifier(namespace=DNFDBUS_NAMESPACE, message_bus=SYSTEM_BUS)

log = getLogger("dnf5dbus")


def gv_list(var: list[str]) -> GLib.Variant:
    return GLib.Variant("as", var)


def gv_bool(var: bool) -> GLib.Variant:
    return GLib.Variant("b", var)


def gv_int(var: int) -> GLib.Variant:
    return GLib.Variant("i", var)


class AsyncDbusCaller:
    def __init__(self):
        self.res = None
        self.loop = None

    def callback(self, call):
        self.res = call()
        self.loop.quit()

    def call(self, mth, *args, **kwargs):
        self.loop = EventLoop()
        mth(*args, **kwargs, callback=self.callback)
        self.loop.run()
        return self.res


class Dnf5Client:
    """context manager for calling the dnf5daemon dbus API

    https://dnf5.readthedocs.io/en/latest/dnf_daemon/dnf5daemon_dbus_api.8.html#interfaces
    """

    def __init__(self) -> None:
        # setup the dnf5daemon dbus proxy
        self.proxy = DNFDBUS.get_proxy()
        self.async_dbus = AsyncDbusCaller()
        # get a session path for the dnf5daemon
        self.session_path = self.proxy.open_session({})
        # setup a proxy for the session object path
        self.session = DNFDBUS.get_proxy(self.session_path)

    def __enter__(self) -> Self:
        """context manager enter, return current object"""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """context manager exit"""
        if exc_type:
            log.critical("", exc_info=(exc_type, exc_value, exc_traceback))
        # close dnf5 session
        self.proxy.close_session(self.session_path)

    def _async_method(self, method: str):
        """create a patial func to make an async call to a given
        dbus method name
        """
        return partial(self.async_dbus.call, getattr(self.session, method))

    def get_list(self, *args, **kwargs) -> list[list[str]]:
        """call the org.rpm.dnf.v0.rpm.Repo list method

        *args is package patterns to match
        **kwargs can contain other options like package_attrs, repo or scope

        """
        options = {}
        options["patterns"] = gv_list(args)
        options["package_attrs"] = gv_list(kwargs.pop("package_attrs", ["nevra"]))
        options["with_src"] = gv_bool(False)
        options["latest-limit"] = gv_int(1)
        if "repo" in kwargs:
            options["repo"] = gv_list(kwargs.pop("repo"))
        if "scope" in kwargs:
            options["scope"] = kwargs.pop("scope")
        # get and async partial function
        get_list = self._async_method("list")
        result = get_list(options)
        # [{
        #   "id": GLib.Variant(),
        #   "nevra": GLib.Variant("s", nevra),
        #   "repo": GLib.Variant("s", repo),
        #   },
        #   {....},
        # ]
        return [
            [value.get_string() for value in list(elem.values())[1:]] for elem in result
        ]


if __name__ == "__main__":
    with Dnf5Client() as client:
        pkgs = client.get_list(
            "dnf*",
            "yum*",
            package_attrs=["nevra", "repo"],
            repo=["fedora", "updates"],
        )
        for (nevra, repo) in pkgs:
            print(f"{nevra:40} repo: {repo}")
