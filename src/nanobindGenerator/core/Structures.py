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
        
class File:
    def __init__(self, filename : str, compilerArgs : list[str] = []):
        self.filename = filename
        self.path = os.path.abspath(filename)
        tu : TranslationUnit = Index.create().parse(self.filename, compilerArgs)
        self.parseFile(tu.cursor, self.path)
        
    def parseFile(self, node : Cursor, file : str):
        isMainFile = node.location.file is not None and (os.path.abspath(str(node.location.file)) == file)
        if isMainFile and node.kind == CursorKind.VAR_DECL and isNodeInGlobalOrNamespaceScope(node):
            print(Variable(node))
            print(node.kind == CursorKind.LAMBDA_EXPR)
        if isMainFile and node.kind == CursorKind.CLASS_DECL:
            pass
        if isMainFile and node.kind == CursorKind.FUNCTION_DECL:
            pass
        for c in node.get_children():
            self.parseFile(c, file)