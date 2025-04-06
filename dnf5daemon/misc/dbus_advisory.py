import datetime
import logging
from functools import partial
from logging import getLogger
from timeit import default_timer as timer
from typing import Any, Self

from dasbus.connection import SystemMessageBus
from dasbus.identifier import DBusServiceIdentifier
from dasbus.loop import EventLoop
from dasbus.typing import get_native, get_variant
from gi.repository import GLib

# Constants
SYSTEM_BUS = SystemMessageBus()
DNFDBUS_NAMESPACE = ("org", "rpm", "dnf", "v0")
DNFDBUS = DBusServiceIdentifier(namespace=DNFDBUS_NAMESPACE, message_bus=SYSTEM_BUS)

logger = getLogger("dnf5dbus")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
    datefmt="%H:%M:%S",
)


# GLib.Variant converters
def gv_list(var: list[str]) -> GLib.Variant:
    return GLib.Variant("as", var)


def gv_str(var: str) -> GLib.Variant:
    return GLib.Variant("s", var)


def gv_bool(var: bool) -> GLib.Variant:
    return GLib.Variant("b", var)


def gv_int(var: int) -> GLib.Variant:
    return GLib.Variant("i", var)


# async call handler class
class AsyncDbusCaller:
    def __init__(self) -> None:
        self.res = None
        self.loop = None

    def callback(self, call) -> None:
        self.res = call()
        self.loop.quit()

    def call(self, mth, *args, **kwargs) -> Any:
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

    def __enter__(self) -> Self:
        """context manager enter, return current object"""
        # get a session path for the dnf5daemon
        self.session_path = self.proxy.open_session({})
        # setup a proxy for the session object path
        self.session = DNFDBUS.get_proxy(self.session_path)
        dnf_interface = ".".join(DNFDBUS_NAMESPACE)
        self.session_repo = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.rpm.Repo")
        self.session_rpm = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.rpm.Rpm")
        self.session_goal = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.Goal")
        self.session_base = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.Base")
        self.session_group = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.comps.Group")
        self.session_advisory = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.Advisory")
        logger.debug(f"Open Dnf5Daemon session: {self.session_path}")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """context manager exit"""
        self.proxy.close_session(self.session_path)
        logger.debug(f"Close Dnf5Daemon session: {self.session_path}")
        if exc_type:
            logger.critical("", exc_info=(exc_type, exc_value, exc_traceback))
        # close dnf5 session

    def _async_method(self, method: str, proxy) -> partial:
        """create a patial func to make an async call to a given
        dbus method name
        """
        return partial(self.async_dbus.call, getattr(proxy, method))

    def advisory_list(self, *args, **kwargs):
        logger.debug(f"\n --> args: {args} kwargs: {kwargs}")
        advisory_attrs = kwargs.pop(
            "advisor_attrs",
            [
                "advisoryid",
                "name",
                "title",
                "type",
                "severity",
                "status",
                "description",
                "buildtime",
                "references",
            ],
        )
        options = {}
        options["advisory_attrs"] = get_variant(list[str], advisory_attrs)
        options["contains_pkgs"] = get_variant(list[str], args)
        options["availability"] = get_variant(str, "all")
        # options[""] = get_variant(list[str], [])
        logger.debug(f" --> options: {options} ")
        get_list = self._async_method("list", proxy=self.session_advisory)
        result = get_list(options)
        return get_native(result)


# package_attrs: list of strings
# list of package attributes that are returned.
# Supported attributes are name, epoch, version, release, arch, repo_id, from_repo_id,
# is_installed, install_size, download_size, buildtime, sourcerpm, summary, url, license,
# description, files, changelogs, provides, requires, requires_pre, conflicts, obsoletes,
#  recommends, suggests, enhances, supplements, evr, nevra, full_nevra, reason, vendor, group.

# dnf5daemon-server is needed to work
if __name__ == "__main__":
    with Dnf5Client() as client:
        # print(client.session.Introspect())
        key = "dnf5"
        print(f"Advisories for {key}")
        t1 = timer()
        upd_info = client.advisory_list(key)
        t2 = timer()
        print(f"execution in {(t2 - t1):.2f}s")
        print(f"Found : {len(upd_info)}")
        print(upd_info)
        for info in upd_info:
            print(info["name"])
            print(info["title"].split(" "))
            print(info["description"])

            timestamp = datetime.datetime.fromtimestamp(info["buildtime"])
            print(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
