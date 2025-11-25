from clang.cindex import Index, CursorKind, Config, Cursor, TranslationUnit, StorageClass, AccessSpecifier
import os
from typing import Optional
from typing import Literal
import clang
import clang.cindex
import argparse
import pickle
import re
# pyright: reportAttributeAccessIssue=false

from .Helper import *

class Variable:
    def __init__(self, node : Cursor):
        self.name = getFullyQualifiedName(node)
        self.plainName = node.spelling
        self.typeStr = node.type.spelling
        self.isArray : bool = node.type.kind.name == 'CONSTANTARRAY'
        self.arraySize : int = node.type.get_array_size() if self.isArray else 0
        self.isExtern : bool = node.storage_class == StorageClass.EXTERN
        self.isLambda : bool = True if re.search("(lambda at *)", self.typeStr) is not None else False
    
    def __str__(self):
        var = f"Variable Properties: fullName [{self.name}]; plainName [{self.plainName}]; "
        var += f"type [{self.typeStr}]; isArray [{self.isArray}]; isExtern [{self.isExtern}]"
        var += f"; isLambda [{self.isLambda}]"
        return var
    
    @property
    def binding(self) -> str | None:
        var = None
        if self.isExtern:
            return var
        if self.isArray:
            lst = f'[&{self.name}]() {{ nb::list lst; for (size_t i = 0; i < {self.arraySize}; ++i) lst.append({self.name}[i]); return lst; }}()'
            return f'm.attr("{self.plainName}") = {lst};'
        if self.isLambda:
            return f'm.def("{self.plainName}", {self.name});'
        var = f'm.attr("{self.plainName}") = {self.name};'
        return var
        
class Function:
    def __init__(self, node : Cursor):
        self.plainName = node.spelling
        self.name = getFullyQualifiedName(node)
        self.paramType, self.paramName = getParameterInfo(node)
        
    @property
    def binding(self) -> str | None:
        if self.paramName[0] != '':
            param_args = ", ".join(f'nb::arg("{name}")' for name in self.paramName)
            param_args = ", " + param_args if param_args else ""
            return f'm.def("{self.plainName}", nb::overload_cast<{", ".join(self.paramType)}>(&{self.name}){param_args});'
        else:
            return f'm.def("{self.plainName}", nb::overload_cast<{", ".join(self.paramType)}>(&{self.name}));'
        
    def __str__(self) -> str:
        func = f"Function Properties: fullName [{self.name}]; plainName [{self.plainName}]; "
        func += f"paramTypes [{self.paramType}]; paramNames [{self.paramName}]"
        return func

class File:
    def __init__(self, filename : str, compilerArgs : list[str] = []):
        self.filename = filename
        self.path = os.path.abspath(filename)
        tu : TranslationUnit = Index.create().parse(self.filename, compilerArgs)
        self.parseFile(tu.cursor, self.path)
        
    def parseFile(self, node : Cursor, file : str):
        isMainFile = node.location.file is not None and (os.path.abspath(str(node.location.file)) == file)
        if isMainFile and node.kind == CursorKind.VAR_DECL and isNodeInGlobalOrNamespaceScope(node):
            print(Variable(node).binding)
        if isMainFile and node.kind == CursorKind.STRUCT_DECL:
            print('struct')
        if isMainFile and node.kind == CursorKind.CLASS_DECL:
            print('class')
        if isMainFile and node.kind == CursorKind.FUNCTION_DECL:
            print(Function(node).binding)
        if isMainFile and node.kind == CursorKind.ENUM_DECL:
            print('enum')
        for c in node.get_children():
            self.parseFile(c, file)