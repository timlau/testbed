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

    def find(self, key):
        # subj = dnf.subject.Subject(key)
        # qa = subj.get_best_query(self.sack, with_provides=False)
        # qa = qa.available()
        nevra = hawkey.split_nevra(key)
        name = nevra.name
        version = nevra.version
        release = nevra.release
        epoch = nevra.epoch
        arch = nevra.arch
        print(f"{name=} {version=}  {release=} {epoch=}, {arch=}")

        q = self.sack.query()
        q = q.installed()
        q = q.filter(
            name=name,
            version=version,
            release=release,
            arch=arch,
            epoch=epoch,
        )
        print("==== latest matching {} =====".format(key))
        for pkg in q.run():
            print("pkg : %-40s repo :  %-20s" % (pkg, pkg.reponame))


if __name__ == "__main__":
    ex = DnfExample()
    ex.find("dnf5daemon-server-5.0.3-20230106005732.1.g1602a9fa.fc37.x86_64")
