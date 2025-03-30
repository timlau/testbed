from timeit import default_timer as timer

import dbus

DNFDAEMON_BUS_NAME = "org.rpm.dnf.v0"
DNFDAEMON_OBJECT_PATH = "/" + DNFDAEMON_BUS_NAME.replace(".", "/")

IFACE_SESSION_MANAGER = "{}.SessionManager".format(DNFDAEMON_BUS_NAME)
IFACE_REPO = "{}.rpm.Repo".format(DNFDAEMON_BUS_NAME)
IFACE_RPM = "{}.rpm.Rpm".format(DNFDAEMON_BUS_NAME)
IFACE_GOAL = "{}.Goal".format(DNFDAEMON_BUS_NAME)


class Dnf5DBus:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.iface_session = dbus.Interface(
            self.bus.get_object(DNFDAEMON_BUS_NAME, DNFDAEMON_OBJECT_PATH),
            dbus_interface=IFACE_SESSION_MANAGER,
        )
        # Prevent loading plugins from host by setting "plugins" to False

    def open_session(self):
        self.session = self.iface_session.open_session({})
        self.iface_repo = dbus.Interface(
            self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
            dbus_interface=IFACE_REPO,
        )
        self.iface_rpm = dbus.Interface(
            self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
            dbus_interface=IFACE_RPM,
        )
        self.iface_goal = dbus.Interface(
            self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
            dbus_interface=IFACE_GOAL,
        )

    def close_session(self):
        self.iface_session.close_session(self.session)

    def repo_list(self):
        result = self.iface_repo.list({"repo_attrs": ["name", "enabled"]})
        # print(result)
        for repo in result:
            print(repo["id"], repo["enabled"])
        return result

    def rpm_list(self, repo):
        result = self.iface_rpm.list(
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
    dnf5dbus = Dnf5DBus()
    dnf5dbus.open_session()
    # get list of available repositories
    repos = dnf5dbus.repo_list()
    # list number of packages in enabled repo
    for repo in repos:
        if repo["enabled"]:
            id = str(repo["id"])
            t1 = timer()
            dnf5dbus.rpm_list(id)
            t2 = timer()
            print(f"execution in {(t2 - t1):.2f}s")
    dnf5dbus.close_session()
