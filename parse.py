import logging
import os
import sys
from pathlib import Path
from typing import List, Generator, Mapping, Optional

import parso
import typer
from pydantic import BaseModel, Field, PrivateAttr, validator
from rich import inspect, print
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


def find_node_docstring(node) -> str:
    docstring = node.get_doc_node()

    if not docstring:
        return EMPTY_STRING

    if isinstance(docstring, parso.python.tree.Leaf):
        return docstring.value

    return str(docstring)


class FunctionDef(BaseModel):
    """A Python function or method definition."""

    docstring: str = EMPTY_STRING
    name: str
    namespace: str
    class_name: str = EMPTY_STRING
    module_name: str = EMPTY_STRING
    package_name: str = EMPTY_STRING
    _parsed: parso.python.tree.Function = PrivateAttr()

    def to_json(self) -> str:
        return self.json(indent=4)

    @classmethod
    def from_parsed_function(
        cls,
        parsed_function: parso.python.tree.Function,
        class_name: str=EMPTY_STRING,
        module_name: str=EMPTY_STRING,
        package_name: str=EMPTY_STRING,
    ) -> "FunctionDef":
        docstring = find_node_docstring(parsed_function)
        name = parsed_function.name.value

        if module_name:
            root_namespace = module_name
        elif package_name:
            root_namespace = package_name
        elif class_name:
            root_namespace = class_name

        if not root_namespace:
            raise ValueError(
                "Make sure a functions's module_name, package_name, or class_name is set"
            )

        namespace = f"{root_namespace}.{name}"
        log.debug("Loading function %s", namespace)
        return cls(
            docstring=docstring,
            name=name,
            namespace=namespace,
            class_name=class_name,
            module_name=module_name,
            package_name=package_name,
            _parsed=parsed_function
        )



class ClassDef(BaseModel):
    """A Python class definition."""

    docstring: str = EMPTY_STRING
    name: str
    namespace: str
    module_name: str = EMPTY_STRING
    package_name: str = EMPTY_STRING
    methods: List[FunctionDef] = Field(default_factory=list)
    _parsed: parso.python.tree.Class = PrivateAttr()

    def all_methods(self) -> Generator[FunctionDef, None, None]:
        for method_def in self.methods:
            yield method_def

    def to_json(self) -> str:
        return self.json(indent=4)

    @classmethod
    def from_parsed_class(
            cls,
            parsed_class: parso.python.tree.Class,
            module_name: str=EMPTY_STRING,
            package_name: str=EMPTY_STRING,
    ) -> "ClassDef":
        docstring = find_node_docstring(parsed_class)
        name = parsed_class.name.value

        if module_name:
            namespace = f"{module_name}.{name}"
        elif package_name:
            namespace = f"{package_name}.{name}"

        if not namespace:
            raise ValueError(
                "Make sure a class's module_name or package_name is set"
            )

        methods = [
            FunctionDef.from_parsed_function(
                parsed_function=funcdef,
                class_name=namespace,
            )
            for funcdef in parsed_class.iter_funcdefs()
        ]

        return cls(
            docstring=docstring,
            name=name,
            namespace=namespace,
            methods=methods,
            module_name=module_name,
            package_name=package_name,
            _parsed=parsed_class
        )

class Module(BaseModel):
    """A Python file with some names defined."""

    namespace: str
    docstring: str = EMPTY_STRING
    classes: List[ClassDef] = Field(default_factory=list)
    functions: List[FunctionDef] = Field(default_factory=list)
    package_name: str = EMPTY_STRING
    _parsed: parso.python.tree.Module = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        log.debug("Loaded module %s", self.namespace)

    def __repr__(self) -> str:
        """Return a string with only the bits we care about."""
        return f"Module(namespace={self.namespace})"

    def __str__(self) -> str:
        """Use the module namespace for stringification"""
        return self.namespace

    def all_classes(self) -> Generator[ClassDef, None, None]:
        for class_def in self.classes:
            yield class_def

    def all_functions(self) -> Generator[FunctionDef, None, None]:
        for function_def in self.functions:
            yield function_def
        for class_def in self.classes:
            yield from class_def.all_methods()

    def to_json(self) -> str:
        return self.json(
            exclude={
                "classes": { "__all__": { "module_name", "package_name" }},
            },
            indent=4,
        )

    @classmethod
    def from_path(
        cls,
        namespace,
        path: Path,
        package_name: str=EMPTY_STRING
    ):
        source = path.read_text()
        parsed = parso.parse(source).get_root_node()
        docstring = find_node_docstring(parsed)
        classes = [
            ClassDef.from_parsed_class(
                classdef,
                module_name=namespace,
            )
            for classdef in parsed.iter_classdefs()
        ]
        functions = [
            FunctionDef.from_parsed_function(
                parsed_function=funcdef,
                module_name=namespace,
            )
            for funcdef in parsed.iter_funcdefs()
        ]

        return cls(
            namespace=namespace,
            docstring=docstring,
            classes=classes,
            functions=functions,
            package_name=package_name,
            _parsed=parsed,
        )


class Package(BaseModel):
    """Indicated by ``__init__.py``."""

    name: str
    docstring: str = EMPTY_STRING
    package_name: str = EMPTY_STRING
    functions: List[FunctionDef] = Field(default_factory=list)
    classes: List[ClassDef] = Field(default_factory=list)
    modules: List[Module] = Field(default_factory=list)
    subpackages: List["Package"] = Field(default_factory=list)
    _package_module: Module = PrivateAttr()
    _path: Path = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        namespace_path = self.name.replace(".", os.path.sep)
        package_path = Path(namespace_path) / "__init__.py"
        self._path = find_in_sys_path(package_path)
        self._package_module = Module.from_path(path=self._path, namespace=self.name)
        self.functions = self._find_functions()
        self.classes = self._find_classes()
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

    def all_classes(self) -> Generator[ClassDef, None, None]:
        for class_def in self.classes:
            yield class_def

        for module in self.modules:
            yield from module.all_classes()

        for subpackage in self.subpackages:
            yield from subpackage.all_classes()

    def all_functions(self) -> Generator[FunctionDef, None, None]:
        for function_def in self.functions:
            yield function_def

        for class_def in self.classes:
            yield from class_def.all_methods()

        for module in self.modules:
            yield from module.all_functions()

        for subpackage in self.subpackages:
            yield from subpackage.all_functions()

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
                "modules": {"__all__": { "classes" } },
                "subpackages": {"__all__": {"subpackages", "modules", "classes"}},
            },
            indent=4,
        )

    def _find_classes(self) -> List[ClassDef]:
        classes = []

        # Not fussing with a deep copy because we should only ever look
        # at my package module *through me*
        for classdef in self._package_module.classes:
            classdef.namespace = f"{self.name}.{classdef.name}"
            classdef.package_name = self.name
            classes.append(classdef)

        return classes

    def _find_functions(self) -> List[FunctionDef]:
        functions = []
        for function_def in self._package_module.functions:
            function_def.namespace = f"{self.name}.{function_def.name}"
            function_def.package_name = self.name
            functions.append(function_def)

        return functions


    def _find_modules(self) -> List[Module]:
        log.debug("Loading modules under %s", self.name)
        module_list = [
            m for m in self._path.parent.glob("*.py") if not m.name.startswith("__")
        ]
        log.debug("module paths found: %s", module_list)
        package_name = self.name

        return [
            Module.from_path(
                path=path,
                package_name=package_name,
                namespace=f"{self.name}.{path.stem}"
            )
            for path in module_list
        ]

    def _find_subpackages(self) -> List["Package"]:
        log.debug("Loading subpackages under %s", self)
        packages = []
        folder_list = [d for d in self._path.parent.iterdir() if d.is_dir()]

        for d in folder_list:
            package_path = d / "__init__.py"

            if package_path.is_file():
                packages.append(
                    Package(
                        name=f"{self.name}.{package_path.parent.stem}",
                        package_name=self.name,
                    )
                )

        log.debug("subpackages found: %s", packages)
        return packages


class CodeLibrary(BaseModel):
    """Tracks all the defined names for serialization."""

    packages: List[Package] = Field(default_factory=list)

    def all_classes(self) -> Generator[ClassDef, None, None]:
        for package in self.packages:
            yield from package.all_classes()

    def all_functions(self) -> Generator[FunctionDef, None, None]:
        for package in self.packages:
            yield from package.all_functions()

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
        class_dir = target_dir / "cls"
        log.info("Serializing classes to %s", class_dir)
        class_dir.mkdir(exist_ok=True)

        for class_def in self.all_classes():
            class_json_path = class_dir / f"{class_def.namespace}.json"
            log.debug("class %s -> %s", class_def, class_json_path)
            class_json_path.write_text(class_def.to_json())

        # functions
        function_dir = target_dir / "def"
        log.info("Serializing functions to %s", function_dir)
        function_dir.mkdir(exist_ok=True)

        for function_def in self.all_functions():
            function_json_path = function_dir / f"{function_def.namespace}.json"
            log.debug("function %s -> %s", function_def, function_json_path)
            function_json_path.write_text(function_def.to_json())

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
