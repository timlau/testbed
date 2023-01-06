from libdnf5.base import Base
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

    def test1(self):
        print("=========> Test1")
        query = PackageQuery(self)
        query.filter_name("dnf*", QueryCmp_IGLOB)
        query.filter_name("yum*", QueryCmp_IGLOB)
        for pkg in query:
            print(pkg.get_nevra())

    def test2(self):
        print("=========> Test2")
        query = PackageQuery(self)
        query.filter_name(["dnf*", "yum*"], QueryCmp_IGLOB)
        for pkg in query:
            print(pkg.get_nevra())

if __name__ == "__main__":
    backend = Backend()
    backend.test1()
    backend.test2()
