from functools import partial
from logging import getLogger
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
DNFDBUS_NAMESPACE = ("org", "rpm", "dnf","v0")
DNFDBUS = DBusServiceIdentifier(
    namespace=DNFDBUS_NAMESPACE,
    message_bus=SYSTEM_BUS
)

log = getLogger("dnfdbus")

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
    
class DnfDbusClient:
    """Wrapper class for the dk.rasmil.DnfDbus Dbus object"""

    def __init__(self):
        self.proxy = DNFDBUS.get_proxy()
        self.async_dbus = AsyncDbusCaller()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            log.debug(f'{exc_type=} {exc_value=} {exc_traceback=}')
        self.quit()

    def get_async_method(self, method):
        return partial(self.async_dbus.call, getattr(self.proxy, method))

    def rpm_list(self):
        call_list = self.get_async_method('list')
        pkgs = call_list({"scope":"installed"})
        
        
if __name__ == "__main__":
    # client = DnfDbusClient()
    # client.rpm_list()

    bus = SystemMessageBus()

    proxy = bus.get_proxy(
        "org.rpm.dnf.v0",
        "/org/rpm/dnf/v0"
    )

    # connect to dnf5 dbus deamon and get a session
    session_path = proxy.open_session({})
    print(f"session : {session_path}")
    # get a new proxy to the new session
    session = bus.get_proxy(
        "org.rpm.dnf.v0",
        session_path
    )
    try:
        # setup option parameters for the list method
        # https://dnf5.readthedocs.io/en/latest/dnf_daemon/dnf5daemon_dbus_api.8.html#org.rpm.dnf.v0.rpm.Rpm.list
        options = {
            'package_attrs': GLib.Variant("as",["nevra","repo"]), # attribues to get
            'repo': GLib.Variant("as",["fedora","updates*","rpmfusion*"]), # limit rpoes
            'patterns': GLib.Variant("as",["dnf*","yum"]), # package globs
            'with_src': GLib.Variant("b",False), # don't get source packages
            'latest-limit' : GLib.Variant("i",1), # only the latest packages
        }
        pkgs = session.list(options)
        for elem in pkgs:
            print(elem["nevra"].get_string(), elem["repo"].get_string())
    except Exception as e:
        # print the exception
        traceback.print_exception(e)
    finally:
        # close the session
        res = proxy.close_session(session_path)
        if res:
            print(f"Session closed : {session_path}")
