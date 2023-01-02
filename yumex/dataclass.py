from dataclasses import dataclass
from typing import Any, Union
from enum import IntEnum


class PackageState(IntEnum):
    UPDATE = 1
    AVAILABLE = 2
    INSTALLED = 3
    DOWNGRADE = 4


class PackageAction(IntEnum):
    DOWNGRADE = 10
    UPGRADE = 20
    INSTALL = 30
    REINSTALL = 40
    ERASE = 50


@dataclass 
class YumexPackage(object):
    name:str
    arch:str 
    epoch:str
    release:str
    version:str
    repo:str
    description:str
    sizeB:int
    state:PackageState
    is_dep:bool = False
    ref_to:Any = None
    action:Union(PackageAction, None) = None
    queued:bool = False
    queue_action:bool = False
    installed=False

    def __init__(self, *args, **kwargs):
        super(YumexPackage, self).__init__(args, kwargs)
    
    @classmethod
    def from_dnf(cls, pkg):
        return cls(
            name=pkg.name, 
            arch=pkg.arch,
            epoch=pkg.epoch,
            release=pkg.release, 
            version=pkg.version, 
            repo=pkg.reponame, 
            description=pkg.summary,
            sizeB=int(pkg.size),
            state=PackageState.AVAILABLE,
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
            sizeB=pkg.get_installed_size(),
            state=state,
        )

    def set_installed(self):
        self.repo = f"@{self.repo}"
        self.installed = True
        self.state = PackageState.INSTALLED

    def set_update(self, inst_pkg):
        self.ref_to = YumexPackage(inst_pkg)
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

#     def __eq__(self, other) -> bool:
#         return self.nevra == other.nevra

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

# class YumexPackageOLD(GObject.GObject):
#     def __init__(self, pkg, state=PackageState.AVAILABLE, action=0):
#         super(YumexPackage, self).__init__()
#         self.queued = False
#         self.queue_action = False  # package being procced by the queue
#         self.name = pkg.name
#         self.arch = pkg.arch
#         self.epoch = pkg.epoch
#         self.release = pkg.release
#         self.version = pkg.version
#         self.repo = pkg.reponame
#         self.description = pkg.summary
#         self.sizeB = int(pkg.size)
#         self.state = state
#         self.is_dep = False
#         self.ref_to = None
#         self.action = action

#     def set_installed(self):
#         self.repo = f"@{self.repo}"
#         self.installed = True
#         self.state = PackageState.INSTALLED

#     def set_update(self, inst_pkg):
#         self.ref_to = YumexPackage(inst_pkg)
#         self.ref_to.state = PackageState.INSTALLED
#         self.state = PackageState.UPDATE

#     @property
#     def size(self):
#         return format_number(self.sizeB)

#     @property
#     def styles(self):
#         match self.state:
#             case PackageState.INSTALLED:
#                 return ["success"]
#             case PackageState.UPDATE:
#                 return ["error"]
#         return []

#     @property
#     def evr(self):
#         if self.epoch:
#             return f"{self.epoch}:{self.version}-{self.release}"
#         else:
#             return f"{self.version}-{self.release}"

#     @property
#     def nevra(self):
#         return f"{self.name}-{self.evr}.{self.arch}"

#     def __repr__(self) -> str:
#         return f"YumexPackage({self.nevra} : {self.repo})"

#     def __eq__(self, other) -> bool:
#         return self.nevra == other.nevra

#     @property
#     def id(self):
#         nevra_r = (
#             self.name,
#             self.epoch,
#             self.version,
#             self.release,
#             self.arch,
#             self.repo[1:],
#         )
#         return ",".join([str(elem) for elem in nevra_r])    
