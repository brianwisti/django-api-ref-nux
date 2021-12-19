import logging
import os
import sys
from pathlib import Path
from typing import List, Generator, Optional

import parso
import typer
from pydantic import BaseModel, Field, PrivateAttr, validator
from rich import print
from rich.logging import RichHandler
from rich.pretty import pprint

logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger(__file__)

EMPTY_STRING = ""
SYS_PATH = [Path(p) for p in sys.path if os.path.isdir(p)]


def find_in_sys_path(file_path: Path) -> Path:
    """Find a specific file somewhere in Python's include path."""
    for sys_path in SYS_PATH:
        child_path = sys_path / file_path

        if child_path.is_file():
            return child_path

    raise ValueError(f"{file_path} not found in sys.path!")


class Module(BaseModel):
    """A Python file with some names defined."""

    path: Path
    docstring: str = EMPTY_STRING
    namespace: str
    _parsed: parso.python.tree.Module = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        source = self.path.read_text()
        self._parsed = parso.parse(source).get_root_node()
        self.docstring = self._find_docstring()
        log.debug("Loaded module %s", self.namespace)

    def __repr__(self) -> str:
        """Return a string with only the bits we care about."""
        return f"Module(namespace={self.namespace})"

    def __str__(self) -> str:
        """Use the module namespace for stringification"""
        return self.namespace

    def _find_docstring(self) -> str:
        """Return the module's plain text docstring if available."""
        docstring = self._parsed.get_doc_node()

        if not docstring:
            return EMPTY_STRING

        if isinstance(docstring, parso.python.tree.Leaf):
            return docstring.value

        return str(docstring)

    @validator("path")
    def path_is_file(cls, path):
        """Validate existence of module file."""
        assert path.is_file(), "must be a file on disk"
        return path

    def to_json(self) -> str:
        return self.json(
            exclude={"path"},
            indent=4,
        )


class Package(BaseModel):
    """Indicated by ``__init__.py``."""

    name: str
    docstring: str = EMPTY_STRING
    modules: List[Module] = Field(default_factory=list)
    subpackages: List["Package"] = Field(default_factory=list)
    _package_module: Module = PrivateAttr()
    _path: Path = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        namespace_path = self.name.replace(".", os.path.sep)
        package_path = Path(namespace_path) / "__init__.py"
        self._path = find_in_sys_path(package_path)
        self._package_module = Module(path=self._path, namespace=self.name)
        self.modules = self._find_modules()
        self.subpackages = self._find_subpackages()
        self.docstring = self._package_module.docstring
        log.debug("Loaded package %s", self)

    def __str__(self) -> str:
        """Use package name for stringification."""
        return self.name

    def __repr__(self) -> str:
        """Return abbreviated info for repr."""
        module_count = len(self.modules)
        subpackage_count = len(self.subpackages)
        return f"Package(name={self.name} modules={module_count}, subpackages={subpackage_count}"

    def all_modules(self) -> Generator[Module, None, None]:
        for module in self.modules:
            yield module

        for subpackage in self.subpackages:
            yield from subpackage.all_modules()

    def all_subpackages(self) -> Generator["Package", None, None]:
        yield self

        for subpackage in self.subpackages:
            yield from subpackage.all_subpackages()

    def to_json(self) -> str:
        return self.json(
            exclude={
                "modules": {"__all__": {"path"}},
                "subpackages": {"__all__": {"subpackages", "modules"}},
            },
            indent=4,
        )

    def _find_modules(self) -> List[Module]:
        log.debug("Loading modules under %s", self.name)
        module_list = [
            m for m in self._path.parent.glob("*.py") if not m.name.startswith("__")
        ]
        log.debug("module paths found: %s", module_list)

        return [
            Module(path=path, namespace=f"{self.name}.{path.stem}")
            for path in module_list
        ]

    def _find_subpackages(self) -> List["Package"]:
        log.debug("Loading subpackages under %s", self)
        packages = []
        folder_list = [d for d in self._path.parent.iterdir() if d.is_dir()]

        for d in folder_list:
            package_path = d / "__init__.py"

            if package_path.is_file():
                packages.append(Package(name=f"{self.name}.{package_path.parent.stem}"))

        log.debug("subpackages found: %s", packages)
        return packages


class CodeLibrary(BaseModel):
    """Tracks all the defined names for serialization."""

    packages: List[Package] = Field(default_factory=list)

    def all_modules(self) -> Generator[Module, None, None]:
        """Return all modules I loaded."""
        for package in self.packages:
            yield from package.all_modules()

    def all_packages(self) -> Generator[Package, None, None]:
        """Return all packages I loaded."""
        for package in self.packages:
            yield from package.all_subpackages()

    def load_package(self, name: str) -> Package:
        pkg = Package(name=name)
        self.packages.append(pkg)
        return pkg

    def serialize(self, target_dir: Path) -> None:
        """Save extracted package details to a data folder."""
        log.info("Serializing code library to %s", target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        package_dir = target_dir / "pkg"
        log.info("Serializing packages to %s", package_dir)
        package_dir.mkdir(exist_ok=True)

        for package in self.all_packages():
            package_json_path = package_dir / f"{package.name}.json"
            log.debug("package %s -> %s", package, package_json_path)
            package_json_path.write_text(package.to_json())

        module_dir = target_dir / "mod"
        log.info("Serializing modules to %s", module_dir)
        module_dir.mkdir(exist_ok=True)

        for module in self.all_modules():
            module_json_path = module_dir / f"{module.namespace}.json"
            log.debug("module %s -> %s", module, module_json_path)
            module_json_path.write_text(module.to_json())

        # classes
        # functions
        # library.json master list
        serialized_self = self.to_json()
        library_path = target_dir / "library.json"
        library_path.write_text(serialized_self)
        log.info("Serialized library summary to %s", library_path)

    def to_json(self) -> str:
        return self.json(include={"packages": {"__all__": {"name"}}}, indent=4)


def main(package_name: str = "django"):
    log.info("Loading package %s", package_name)
    library = CodeLibrary()
    package = library.load_package(package_name)
    log.info("Finished loading %s", package)
    data_dir = Path("content")
    library.serialize(data_dir)


if __name__ == "__main__":
    typer.run(main)
