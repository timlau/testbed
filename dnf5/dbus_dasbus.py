import json
import logging
import os
import select
from functools import partial
from logging import getLogger
from timeit import default_timer as timer
from typing import Any, Self

from dasbus.connection import SystemMessageBus
from dasbus.identifier import DBusServiceIdentifier
from dasbus.loop import EventLoop
from dasbus.typing import get_native, get_variant
from dasbus.unix import GLibClientUnix
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


class Dnf5DBusClient:
    """context manager for calling the dnf5daemon dbus API

    https://dnf5.readthedocs.io/en/latest/dnf_daemon/dnf5daemon_dbus_api.8.html#interfaces
    """

    def __init__(self) -> None:
        # setup the dnf5daemon dbus proxy
        self.proxy = DNFDBUS.get_proxy(client=GLibClientUnix)
        self.async_dbus = AsyncDbusCaller()
        self.connected = False

    def __enter__(self) -> Self:
        """context manager enter, return current object"""
        # get a session path for the dnf5daemon
        self.open_connection()
        return self

    def open_connection(self):
        if not self.connected:
            self.session_path = self.proxy.open_session({})
            self.connected = True
            # setup a proxy for the session object path
            self.session = DNFDBUS.get_proxy(self.session_path)
            self.session_repo = DNFDBUS.get_proxy(
                self.session_path,
                interface_name="org.rpm.dnf.v0.rpm.Repo",
                client=GLibClientUnix,
            )
            self.session_rpm = DNFDBUS.get_proxy(
                self.session_path,
                interface_name="org.rpm.dnf.v0.rpm.Rpm",
                client=GLibClientUnix,
            )

            self.session_goal = DNFDBUS.get_proxy(
                self.session_path,
                interface_name="org.rpm.dnf.v0.Goal",
                client=GLibClientUnix,
            )
            self.session_base = DNFDBUS.get_proxy(
                self.session_path,
                interface_name="org.rpm.dnf.v0.Base",
                client=GLibClientUnix,
            )
            self.session_advisory = DNFDBUS.get_proxy(
                self.session_path,
                interface_name="org.rpm.dnf.v0.Advisory",
                client=GLibClientUnix,
            )
            logger.debug(f"Open Dnf5Daemon session: {self.session_path}")
        else:
            logger.debug(f"Connection already open : {self.session_path}")

    def close_connection(self):
        if self.connected:
            self.proxy.close_session(self.session_path)
            logger.debug(f"Close Dnf5Daemon session: {self.session_path}")
        else:
            logger.debug("No open connection")

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """context manager exit"""
        self.close_connection()
        if exc_type:
            logger.critical("", exc_info=(exc_type, exc_value, exc_traceback))
        # close dnf5 session

    def _async_method(self, method: str, proxy=None) -> partial:
        """create a patial func to make an async call to a given
        dbus method name
        """
        if not proxy:
            proxy = self.session
        return partial(self.async_dbus.call, getattr(proxy, method))

    def repo_list(self):
        repos = self.session_repo.list(
            {"repo_attrs": get_variant(list[str], ["name", "enabled"])}
        )
        return get_native(repos)

    def package_list(self, *args, **kwargs) -> list[list[str]]:
        """call the org.rpm.dnf.v0.rpm.Repo list method

        *args is package patterns to match
        **kwargs can contain other options like package_attrs, repo or scope

        """
        package_attrs = kwargs.pop("package_attrs", ["nevra"])
        options = {}
        options["patterns"] = get_variant(list[str], args)  # gv_list(args)
        options["package_attrs"] = get_variant(list[str], package_attrs)
        options["with_src"] = get_variant(bool, False)
        options["icase"] = get_variant(bool, True)
        # options["latest-limit"] = get_variant(int, 1)
        if "repo" in kwargs:
            options["repo"] = get_variant(list[str], kwargs.pop("repo"))
        # limit packages to one of “all”, “installed”, “available”, “upgrades”, “upgradable”
        if "scope" in kwargs:
            options["scope"] = get_variant(str, kwargs.pop("scope"))
        # get and async partial function
        get_list = self._async_method("list", self.session_rpm)
        result = get_list(options)
        # [{
        #   "id": GLib.Variant(),
        #   "nevra": GLib.Variant("s", nevra),
        #   "repo": GLib.Variant("s", repo),
        #   },
        #   {....},
        # ]

        return get_native(result)

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
                "vendor",
                "description",
            ],
        )
        options = {}
        options["advisory_attrs"] = get_variant(list[str], advisory_attrs)
        # options["contains_pkgs"] = get_variant(list[str], args)
        options["availability"] = get_variant(str, "all")
        # options[""] = get_variant(list[str], [])
        logger.debug(f" --> options: {options} ")
        get_list = self._async_method("list", proxy=self.session_advisory)
        result = get_list(options)
        return get_native(result)

    def _list_fd(self, options):
        """Generator function that yields packages as they arrive from the server."""

        # create a pipe and pass the write end to the server
        pipe_r, pipe_w = os.pipe()
        # transfer id serves as an identifier of the pipe transfer for a signal emitted
        # after server finish. This example does not use it.
        print(pipe_w, type(pipe_w))
        transfer_id = self.session_rpm.list_fd(options, pipe_w)
        logger.debug(f"list_fd: transfer_id : {transfer_id}")
        # close the write end - otherwise poll cannot detect the end of transmission
        os.close(pipe_w)

        # decoder that will be used to parse incomming data
        parser = json.JSONDecoder()

        # prepare for polling
        poller = select.poll()
        poller.register(pipe_r, select.POLLIN)
        # wait for data 10 secs at most
        timeout = 60000
        # 64k is a typical size of a pipe
        buffer_size = 65536

        # remaining string to parse (can contain unfinished json from previous run)
        to_parse = ""
        # remaining raw data (i.e. data before UTF decoding)
        raw_data = b""
        while True:
            # wait for data
            polled_event = poller.poll(timeout)
            if not polled_event:
                print("Timeout reached.")
                break

            # we know there is only one fd registered in poller
            descriptor, event = polled_event[0]
            # read a chunk of data
            buffer = os.read(descriptor, buffer_size)
            if not buffer:
                # end of file
                break

            raw_data += buffer
            try:
                to_parse += raw_data.decode()
                # decode successful, clear remaining raw data
                raw_data = b""
            except UnicodeDecodeError:
                # Buffer size split data in the middle of multibyte UTF character.
                # Need to read another chunk of data.
                continue

            # parse JSON objects from the string
            while to_parse:
                try:
                    # skip all chars till begin of next JSON objects (new lines mostly)
                    json_obj_start = to_parse.find("{")
                    if json_obj_start < 0:
                        break
                    obj, end = parser.raw_decode(to_parse[json_obj_start:])
                    yield obj
                    to_parse = to_parse[(json_obj_start + end) :]
                except json.decoder.JSONDecodeError:
                    # this is just example which assumes that every decode error
                    # means the data are incomplete (buffer size split the json
                    # object in the middle). So the handler does not do anything
                    # just break the parsing cycle and continue polling.
                    break

    def package_list_fd(self, *args, **kwargs):
        package_attrs = kwargs.pop("package_attrs", ["nevra"])
        options = {}
        options["patterns"] = get_variant(list[str], args)  # gv_list(args)
        options["package_attrs"] = get_variant(list[str], package_attrs)
        options["with_src"] = get_variant(bool, False)
        options["icase"] = get_variant(bool, True)
        # options["latest-limit"] = get_variant(int, 1)
        if "repo" in kwargs:
            options["repo"] = get_variant(list[str], kwargs.pop("repo"))
        # limit packages to one of “all”, “installed”, “available”, “upgrades”, “upgradable”
        if "scope" in kwargs:
            options["scope"] = get_variant(str, kwargs.pop("scope"))
        # get and async partial function

        result = list(self._list_fd(options))
        # print(result)
        return get_native(result)


# package_attrs: list of strings
# list of package attributes that are returned.
# Supported attributes are name, epoch, version, release, arch, repo_id, from_repo_id,
# is_installed, install_size, download_size, buildtime, sourcerpm, summary, url, license,
# description, files, changelogs, provides, requires, requires_pre, conflicts, obsoletes,
#  recommends, suggests, enhances, supplements, evr, nevra, full_nevra, reason, vendor, group.

# dnf5daemon-server is needed to work
if __name__ == "__main__":
    with Dnf5DBusClient() as client:
        # print(client.session.Introspect())
        package_attrs = ["nevra", "repo_id", "summary"]
        key = "*"
        print(f"Searching for {key}")
        t1 = timer()
        pkgs = client.package_list_fd("a*", repo="fedora")
        t2 = timer()
        print(f"execution in {(t2 - t1):.2f}s")
        print(len(pkgs))
