import re
import sys
import weakref

from gi.repository import Gio, GLib, GObject

ORG = "org.rpm.dnf.v0"
INTERFACE = ORG

DBUS_ERR_RE = re.compile(r".*GDBus.Error:([\w\.]*): (.*)$")
OBJECT_PATH = "/" + ORG.replace(".", "/")


#
# Helper Classes
#


class DBus:
    """Helper class to work with GDBus in a easier way"""

    def __init__(self, conn):
        self.conn = conn

    def get(self, bus, obj, iface=None):
        if iface is None:
            iface = bus
        return Gio.DBusProxy.new_sync(self.conn, 0, None, bus, obj, iface, None)

    def get_async(self, callback, bus, obj, iface=None):
        if iface is None:
            iface = bus
        Gio.DBusProxy.new(self.conn, 0, None, bus, obj, iface, None, callback, None)


class WeakMethod:
    """Helper class to work with a weakref class method"""

    def __init__(self, inst, method):
        self.proxy = weakref.proxy(inst)
        self.method = method

    def __call__(self, *args):
        return getattr(self.proxy, self.method)(*args)


# Get the system bus
system = DBus(Gio.bus_get_sync(Gio.BusType.SYSTEM, None))


class Dnf5Daemon:
    def __init__(self, bus=system, org=ORG, interface=INTERFACE):
        self.bus = bus
        self.dbus_org = org
        self.dbus_interface = interface
        self.daemon = self._get_daemon(bus, org, interface)

    def _get_daemon(self, bus, org, interface):
        """Get the daemon dbus proxy object"""
        try:
            proxy = self.bus.get(org, "/", interface)
            # Get daemon version, to check if it is alive
            # Connect the Dbus signal handler
            proxy.connect("g-signal", WeakMethod(self, "_on_g_signal"))
            return proxy
        except Exception as err:
            self._handle_dbus_error(err)

    def _on_g_signal(self, proxy, sender, signal, params):
        """DBUS signal Handler"""
        args = params.unpack()  # unpack the glib variant
        self.handle_dbus_signals(proxy, sender, signal, args)

    def handle_dbus_signals(self, proxy, sender, signal, args):
        """Overload in child class"""
        pass

    def _handle_dbus_error(self, err):
        """Parse error from service and raise python Exceptions"""
        exc, msg = self._parse_error()
        print(msg)

    def _parse_error(self):
        """parse values from a DBus releated exception"""
        (type, value, traceback) = sys.exc_info()
        res = DBUS_ERR_RE.match(str(value))
        if res:
            return res.groups()
        return "", ""

    def _return_handler(self, obj, result, user_data):
        """Async DBus call, return handler"""
        if isinstance(result, Exception):
            # print(result)
            user_data["result"] = None
            user_data["error"] = result
        else:
            user_data["result"] = result
            user_data["error"] = None
        user_data["main_loop"].quit()

    def _get_result(self, user_data):
        """Get return data from async call or handle error

        user_data:
        """
        if user_data["error"]:  # Errors
            self._handle_dbus_error(user_data["error"])
        else:
            return user_data["result"]

    def _run_dbus_async(self, cmd, *args):
        """Make an async call to a DBus method in the yumdaemon service

        cmd: method to run
        """
        main_loop = GLib.MainLoop()
        data = {"main_loop": main_loop}
        func = getattr(self.daemon, cmd)
        # timeout = infinite
        func(
            *args,
            result_handler=self._return_handler,
            user_data=data,
            timeout=GObject.G_MAXINT,
        )
        data["main_loop"].run()
        result = self._get_result(data)
        return result

    def _run_dbus_sync(self, cmd, *args):
        """Make a sync call to a DBus method in service
        cmd:
        """
        func = getattr(self.daemon, cmd)
        return func(*args)


if __name__ == "__main__":
    dnf5 = system.get(ORG, OBJECT_PATH, INTERFACE + ".SessionManager")
    print(dnf5)
    session = dnf5.open_session(("(a{sv})", {}))
    dnf5.close_session(session)
