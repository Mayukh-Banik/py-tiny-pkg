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