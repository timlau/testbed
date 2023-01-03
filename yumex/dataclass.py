from dataclasses import dataclass
from typing import Any, Union
from enum import IntEnum


class PackageState(IntEnum):
    UPDATE = 1
    AVAILABLE = 2
    INSTALLED = 3
    DOWNGRADE = 4


class PackageAction(IntEnum):
    NONE = 0
    DOWNGRADE = 10
    UPGRADE = 20
    INSTALL = 30
    REINSTALL = 40
    ERASE = 50


class GObject:
    type = "Gobject"

class YumexPackage(GObject):

    def __init__(self, *args, **kwargs):
        super(YumexPackage, self).__init__()
        self.name:str = kwargs.pop("name")
        self.arch:str = kwargs.pop("arch")
        self.epoch:str = kwargs.pop("epoch")
        self.release:str= kwargs.pop("release")
        self.version:str= kwargs.pop("version")
        self.repo:str= kwargs.pop("repo")
        self.description:str= kwargs.pop("description")
        self.sizeB:int= kwargs.pop("size")
        self.state:PackageState = kwargs.pop("state",PackageState.AVAILABLE)
        self.action:PackageAction = kwargs.pop("state",PackageAction.NONE)
        self.is_dep:bool = False
        self.ref_to:YumexPackage = None
        self.queued:bool = False
        self.queue_action:bool = False
    
    @classmethod
    def from_dnf4(cls, pkg):
        return cls(
            name=pkg.name, 
            arch=pkg.arch,
            epoch=pkg.epoch,
            release=pkg.release, 
            version=pkg.version, 
            repo=pkg.reponame, 
            description=pkg.summary,
            size=int(pkg.size),
        )

    @classmethod
    def from_dnf5(cls, pkg):
        if pkg.is_installed():
            state = PackageState.INSTALLED
        else:
            state = PackageState.AVAILABLE
        return cls(
            name=pkg.get_name(), 
            arch=pkg.get_arch(),
            epoch=pkg.get_epoch(),
            release=pkg.get_release(), 
            version=pkg.get_version(), 
            repo=pkg.get_repo_id(), 
            description=pkg.get_summary(),
            size=pkg.get_install_size(),
            state=state,
        )

    @property
    def installed(self):
        return self.state == PackageState.INSTALLED

    def set_installed(self):
        self.repo = f"@{self.repo}"
        self.state = PackageState.INSTALLED

    def set_update(self, inst_pkg):
        self.ref_to = YumexPackage.from_dnf4(inst_pkg)
        self.ref_to.state = PackageState.INSTALLED
        self.state = PackageState.UPDATE

#     @property
#     def size(self):
#         return format_number(self.sizeB)

    # @property
    # def styles(self):
    #     match self.state:
    #         case PackageState.INSTALLED:
    #             return ["success"]
    #         case PackageState.UPDATE:
    #             return ["error"]
    #     return []

    @property
    def evr(self):
        if self.epoch:
            return f"{self.epoch}:{self.version}-{self.release}"
        else:
            return f"{self.version}-{self.release}"

    @property
    def nevra(self):
        return f"{self.name}-{self.evr}.{self.arch}"

    def __str__(self) -> str:
        return f"YumexPackage({self.nevra} : {self.repo})"

    def __eq__(self, other) -> bool:
        return self.nevra == other.nevra

    @property
    def id(self):
        nevra_r = (
            self.name,
            self.epoch,
            self.version,
            self.release,
            self.arch,
            self.repo[1:],
        )
        return ",".join([str(elem) for elem in nevra_r])    

