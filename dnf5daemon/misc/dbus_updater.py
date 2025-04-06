import dbus

UPDATER_BUS_NAME = "dk.yumex.UpdateService"
UPDATER_OBJECT_PATH = "/" + UPDATER_BUS_NAME.replace(".", "/")

try:
    bus = dbus.SessionBus()
    updater_iface = dbus.Interface(
        bus.get_object(UPDATER_BUS_NAME, UPDATER_OBJECT_PATH),
        dbus_interface=UPDATER_BUS_NAME,
    )
    updater_iface.RefreshUpdates(True)
    print(f"{UPDATER_BUS_NAME}.RefreshUpdates called")

except dbus.DBusException as e:
    match e.get_dbus_name():
        case "org.freedesktop.DBus.Error.ServiceUnknown":
            print(f" {UPDATER_BUS_NAME} is not running")
        case _:
            print(e.get_dbus_message())
            print(e.get_dbus_name())
