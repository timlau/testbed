import hawkey
import dnf.subject

from base import DnfBase


class DnfExample(DnfBase):
    """
    This examples shows how to use the dnf.subject.Subject to
    find packages matching a wildcard like yum*
    """

    def __init__(self):
        DnfBase.__init__(self)

    def updates(self):
        q = self.sack.query()
        q = q.upgrades().filter(arch__neq="src").run()
        for pkg in sorted(q):
            print("pkg : %-40s repo :  %-20s" % (pkg, pkg.reponame))


if __name__ == "__main__":
    ex = DnfExample()
    ex.updates()
