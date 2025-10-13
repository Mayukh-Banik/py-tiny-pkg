from clang.cindex import Index, CursorKind, Config, Cursor, TranslationUnit, StorageClass, AccessSpecifier
import os
from typing import Optional
from typing import Literal
import clang
import clang.cindex
import argparse
# pyright: reportAttributeAccessIssue=false