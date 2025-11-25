from clang.cindex import Index, CursorKind, Config, Cursor, TranslationUnit, StorageClass, AccessSpecifier
import os
from typing import Optional
from typing import Literal
import clang
import clang.cindex
import argparse
import yaml
from sys import stderr
# pyright: reportAttributeAccessIssue=false

def isNodeInGlobalOrNamespaceScope(node: Cursor) -> bool:
    """Check if a node is at global or namespace scope (not inside a class/struct)."""
    parent = node.semantic_parent
    while parent is not None:
        if parent.kind in [CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]:
            return False
        if parent.kind == CursorKind.TRANSLATION_UNIT:
            return True
        parent = parent.semantic_parent
    return True

def getFullyQualifiedName(node: Cursor) -> str:
    parts = []
    cur = node
    while cur is not None and cur.kind != CursorKind.TRANSLATION_UNIT:
        if cur.spelling:  
            parts.append(cur.spelling)
        cur = cur.semantic_parent
    return "::".join(reversed(parts))

def getFullyQualifiedTypeName(type_obj) -> str:
    """Get the fully qualified name of a type, resolving through typedefs and pointers."""
    if type_obj.kind.name == 'POINTER':
        pointee = type_obj.get_pointee()
        return getFullyQualifiedTypeName(pointee) + ' *'
    if type_obj.kind.name == 'LVALUEREFERENCE':
        referenced = type_obj.get_pointee()
        return getFullyQualifiedTypeName(referenced) + ' &'
    if type_obj.kind.name == 'RVALUEREFERENCE':
        referenced = type_obj.get_pointee()
        return getFullyQualifiedTypeName(referenced) + ' &&'
    canonical = type_obj.get_canonical()
    decl = canonical.get_declaration()
    if decl and decl.kind != CursorKind.NO_DECL_FOUND:
        return getFullyQualifiedName(decl)
    return type_obj.spelling

def getParameterInfo(node: Cursor) -> tuple[list[str], list[str]]:
    """Extract parameter types and fully qualified names from a function/constructor."""
    param_types = []
    param_names = []
    for arg in node.get_arguments():
        param_types.append(getFullyQualifiedTypeName(arg.type))
        param_names.append(arg.spelling)
    return param_types, param_names