

import libdnf5.base as base
from libdnf5.base import Base,Goal,Transaction_transaction_result_to_string, TransactionPackage
from libdnf5.rpm import PackageQuery, Package  # noqa: F401
from libdnf5.repo import RepoQuery, Repo  # noqa : F401
from libdnf5.common import QueryCmp_NEQ, QueryCmp_NOT_IGLOB, QueryCmp_ICONTAINS, QueryCmp_IGLOB # noqa : F401

class Backend(Base):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.load_config_from_file()
        self.setup()
        self.repo_sack = self.get_repo_sack()
        self.repo_sack.create_repos_from_system_configuration()
        self.repo_sack.update_and_load_enabled_repos(True)
        
    def get_action(self, action):
        match action:
            case base.GoalAction_INSTALL:
                msg = f"install({action})"
            case base.GoalAction_INSTALL_OR_REINSTALL:
                msg = f"install/reinstall({action})"                
            case base.GoalAction_UPGRADE:
                msg = "update"                
            case base.GoalAction_REMOVE:
                msg = "remove"                
            # case base.GoalAction_:
            #     msg = ""                
            case _:
                msg = f"action({action})"
        return msg

    def test(self):
        print("=========> Test2")
        query = PackageQuery(self)
        query.filter_available()
        query.filter_latest_evr()
        query.filter_name(["0xFFFF"])
        print(query.size())
        goal = Goal(self)
        for pkg in query:
            print(pkg.get_nevra(), pkg.is_installed())
            goal.add_rpm_install(pkg.get_nevra())

        transaction = goal.resolve()
        print("Resolved transaction:")
        tspkg: TransactionPackage
        for tspkg in transaction.get_transaction_packages():
            nevra = tspkg.get_package().get_nevra() 
            action = tspkg.get_action()
            state = tspkg.get_state()
            reason = tspkg.get_reason()
            print(f"  {nevra} action: {self.get_action(action)} state: {state} reason: {reason}")


if __name__ == "__main__":
    backend = Backend()
    backend.test()
