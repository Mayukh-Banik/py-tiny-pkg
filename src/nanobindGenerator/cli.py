from clang.cindex import Index, CursorKind, Config, Cursor, TranslationUnit, StorageClass, AccessSpecifier
import os
from typing import Optional
from typing import Literal
import clang
import clang.cindex
import argparse
import yaml

# pyright: reportAttributeAccessIssue=false

# def getFullyQualifiedName(node: Cursor) -> str:
#     parts = []
#     cur = node
#     while cur is not None and cur.kind != CursorKind.TRANSLATION_UNIT:
#         if cur.spelling:  
#             parts.append(cur.spelling)
#         cur = cur.semantic_parent
#     return "::".join(reversed(parts))

# def getAccessSpecifier(node: Cursor) -> Literal["public", "protected", "private", "unknown"]:
#     access = node.access_specifier
#     if access == AccessSpecifier.PUBLIC:
#         return "public"
#     elif access == AccessSpecifier.PROTECTED:
#         return "protected"
#     elif access == AccessSpecifier.PRIVATE:
#         return "private"
#     else:
#         return "unknown"

# def getFullyQualifiedTypeName(type_obj) -> str:
#     """Get the fully qualified name of a type, resolving through typedefs and pointers."""
#     if type_obj.kind.name == 'POINTER':
#         pointee = type_obj.get_pointee()
#         return getFullyQualifiedTypeName(pointee) + ' *'
#     if type_obj.kind.name == 'LVALUEREFERENCE':
#         referenced = type_obj.get_pointee()
#         return getFullyQualifiedTypeName(referenced) + ' &'
#     if type_obj.kind.name == 'RVALUEREFERENCE':
#         referenced = type_obj.get_pointee()
#         return getFullyQualifiedTypeName(referenced) + ' &&'
#     canonical = type_obj.get_canonical()
#     decl = canonical.get_declaration()
#     if decl and decl.kind != CursorKind.NO_DECL_FOUND:
#         return getFullyQualifiedName(decl)
#     return type_obj.spelling

# def getParameterInfo(node: Cursor) -> tuple[list[str], list[str]]:
#     """Extract parameter types and fully qualified names from a function/constructor."""
#     param_types = []
#     param_names = []
#     for arg in node.get_arguments():
#         param_types.append(getFullyQualifiedTypeName(arg.type))
#         param_names.append(arg.spelling)
#     return param_types, param_names

# class Field:
#     def __init__(self, node: Cursor):
#         self.dataName: str = getFullyQualifiedName(node)
#         self.accessStatus = getAccessSpecifier(node)
#         self.isConst = node.type.is_const_qualified()
#         self.dataType = node.type.spelling
        
#     def __str__(self) -> str:
#         if self.accessStatus == "protected" or self.accessStatus == "private":
#             return ""
#         if self.isConst:
#             return f'.def_ro("{self.dataName}", &{self.dataName})'
#         else:
#             return f'.def_rw("{self.dataName}", &{self.dataName})'
    
# class StaticField:
#     def __init__(self, node: Cursor):
#         self.dataName = getFullyQualifiedName(node)
#         self.accessStatus = getAccessSpecifier(node)
#         self.isConst = node.type.is_const_qualified()
#         self.dataType = node.type.spelling
        
#     def __str__(self) -> str:
#         if self.accessStatus == "protected" or self.accessStatus == "private":
#             return ""
#         if self.isConst:
#             return f'.def_ro_static("{self.dataName}", &{self.dataName})'
#         else:
#             return f'.def_rw_static("{self.dataName}", &{self.dataName})'
    
# class Constructor:
#     def __init__(self, node: Cursor):
#         self.name = getFullyQualifiedName(node)
#         self.accessStatus = getAccessSpecifier(node)
#         self.paramType, self.paramName = getParameterInfo(node)
#         self.isConvertingConstructor = node.is_converting_constructor()
#         self.isCopyConstructor = node.is_copy_constructor()
#         self.isDefaultConstructor = node.is_default_constructor()
#         self.isMoveConstructor = node.is_move_constructor()
        
#     def __str__(self) -> str:
#         if self.isDefaultConstructor:
#             return ".def(nb::init<>())"
#         elif self.isCopyConstructor:
#             return f'.def(nb::init<{self.paramType[0]}>(nb::arg(other)))'
#         elif self.isMoveConstructor:
#             return f'.def(nb::init<{self.paramType[0]}>(nb::arg(other)))'
#         param_args = "(" + ", ".join(f'nb::arg("{name}")' for name in self.paramName) + ")"
#         return f'.def(nb::init<{", ".join(self.paramType)}>{param_args})'

# class Method:
#     def __init__(self, node : Cursor, clsName : str):
#         self.plainName = node.spelling
#         self.clsName = clsName
#         self.name = getFullyQualifiedName(node)
#         self.paramType, self.paramName = getParameterInfo(node)
#         self.accessStatus = getAccessSpecifier(node)
#         self.returnType = node.result_type.spelling 
#         self.isConst = node.is_const_method() 
#         self.isStatic = node.is_static_method()
#         self.isVirtual = node.is_virtual_method()
#         self.isPureVirtual = node.is_pure_virtual_method() 
#         self.isDeleted = node.is_deleted_method()
#         self.isDefault = node.is_default_method() 
#         self.isCopyAssignment = node.is_copy_assignment_operator_method()
#         self.isMoveAssignment = node.is_move_assignment_operator_method()
    
#     def __str__(self) -> str:
#         param_args = ", ".join(f'nb::arg("{name}")' for name in self.paramName)
#         param_args = ", " + param_args if param_args else ""
#         if self.isCopyAssignment:
#             t = f'.def("__copy__", [](const {self.clsName}& self){{return {self.clsName}(self); }})'
#             g = f'.def("__deepcopy__", [](const {self.clsName}& self, nb::dict){{return {self.clsName}(self); }})'
#             return t + '\n' + g
#         elif self.isMoveAssignment:
#             return ''
#         elif self.isDeleted:
#             return ''
#         elif self.isPureVirtual:
#             return ''
#         elif self.isStatic:
#             return f'.def_static("{self.plainName}", nb::overload_cast<{", ".join(self.paramType)}>(&{self.name}){param_args})'
#         return f'.def("{self.plainName}", nb::overload_cast<{", ".join(self.paramType)}>(&{self.name}){param_args})'
    
# class Class:
#     def __init__(self, class_node: Cursor):
#         self.classNode = class_node
#         self.className = getFullyQualifiedName(self.classNode)
#         self.constructors : list[Constructor] = []
#         self.methods = []
#         self.static_methods = []
#         self.fields : list[Field] = []
#         self.static_fields : list[StaticField] = []
#         self.nested_classes = []
#         self.enums = []
#         self.typedefs = []
#         self.friends = []
        
#         for member in class_node.get_children():
#             access = getAccessSpecifier(member)
#             if access != 'public':
#                 continue
#             member : Cursor = member
#             if member.kind == CursorKind.CONSTRUCTOR:
#                 self.constructors.append(Constructor(member))
#             elif member.kind == CursorKind.DESTRUCTOR:
#                 pass
#             elif member.kind == CursorKind.CXX_METHOD:
#                 if member.is_static_method():
#                     self.static_methods.append(Method(member, self.className))
#                 else:
#                     self.methods.append(Method(member, self.className))
                    
#             elif member.kind == CursorKind.FIELD_DECL:
#                 self.fields.append(Field(member))
                
#             elif member.kind == CursorKind.VAR_DECL:
#                 if member.storage_class == StorageClass.STATIC:
#                     self.static_fields.append(StaticField(member))
                    
#             elif member.kind == CursorKind.CLASS_DECL or member.kind == CursorKind.STRUCT_DECL:
#                 pass
                
#             elif member.kind == CursorKind.ENUM_DECL:
#                 info = f"  [{access}] enum {member.spelling}"
#                 self.enums.append(info)
                
#             elif member.kind == CursorKind.TYPEDEF_DECL or member.kind == CursorKind.TYPE_ALIAS_DECL:
#                 info = f"  [{access}] typedef/using {member.spelling} = {member.underlying_typedef_type.spelling}"
#                 self.typedefs.append(info)
                
#             elif member.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
#                 continue
                
#             elif member.kind == CursorKind.FRIEND_DECL:
#                 pass
                
#     def __str__(self) -> str:
#         return ""

# class Variable:
#     def __init__(self, node: Cursor):
#         self.name = getFullyQualifiedName(node)
#         self.plainName = node.spelling
#         self.type = node.type
#         self.isArray = node.type.kind.name == 'CONSTANTARRAY'
#         self.arraySize = node.type.get_array_size() if self.isArray else None
        
       
#     def __str__(self) -> str:
#         if self.isArray:
#             list_init = f'[&]() {{ nb::list lst; for (size_t i = 0; i < {self.arraySize}; ++i) lst.append({self.name}[i]); return lst; }}()'
#             return f'm.attr("{self.plainName}") = {list_init};'
        
#         return f'm.attr("{self.plainName}") = {self.name};'
    
# class Function:
#     def __init__(self, node : Cursor):
#         self.plainName = node.spelling
#         self.name = getFullyQualifiedName(node)
#         self.paramType, self.paramName = getParameterInfo(node)
        
#     def __str__(self) -> str:
#         param_args = ", ".join(f'nb::arg("{name}")' for name in self.paramName)
#         param_args = ", " + param_args if param_args else ""
#         return f'm.def("{self.plainName}", nb::overload_cast<{", ".join(self.paramType)}>(&{self.name}){param_args});'

# def is_global_or_namespace_scope(node: Cursor) -> bool:
#     """Check if a node is at global or namespace scope (not inside a class/struct)."""
#     parent = node.semantic_parent
#     while parent is not None:
#         if parent.kind in [CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]:
#             return False
#         if parent.kind == CursorKind.TRANSLATION_UNIT:
#             return True
#         parent = parent.semantic_parent
#     return True

# class File:
#     def __init__(self, filename : str):
#         self.filenameRelative = filename
#         self.list : list = []
#         index: Index = Index.create()
#         tu: TranslationUnit = index.parse(filename, args=["-std=c++17"])
#         main_file: str = os.path.abspath(filename)
#         self.parseFile(tu.cursor, main_file)
    
#     def write_to_file(self):
#         directory = os.path.dirname(self.filenameRelative)
#         base_name = os.path.splitext(os.path.basename(self.filenameRelative))[0]
#         output_filename = os.path.join(directory, f'bindingsFor{base_name}.hpp')
#         with open(output_filename, 'w') as f:
#             f.write(str(self))
#         print(f"Bindings written to: {output_filename}")
        
#     def parseFile(self, node : Cursor, file : str):
#         isMainFile = node.location.file is not None and (os.path.abspath(str(node.location.file)) == file)
#         if isMainFile and node.kind == CursorKind.VAR_DECL and is_global_or_namespace_scope(node):
#             self.list.append(Variable(node))
#         if isMainFile and node.kind == CursorKind.CLASS_DECL:
#             self.list.append(Class(node))
#         if isMainFile and node.kind == CursorKind.FUNCTION_DECL:
#             self.list.append(Function(node))
#         for c in node.get_children():
#             self.parseFile(c, file)
        
#     def __str__(self) -> str:
#         header = f'// Generated from {self.filenameRelative}\n\n'
#         header += f'#include "{self.filenameRelative}"\n'
#         header += '#include <nanobind/nanobind.h>\n'
#         header += '#include <nanobind/stl/array.h>\n'
#         header += '#include <nanobind/stl/chrono.h>\n'
#         header += '#include <nanobind/stl/complex.h>\n'
#         header += '#include <nanobind/stl/filesystem.h>\n'
#         header += '#include <nanobind/stl/function.h>\n'
#         header += '#include <nanobind/stl/list.h>\n'
#         header += '#include <nanobind/stl/map.h>\n'
#         header += '#include <nanobind/stl/optional.h>\n'
#         header += '#include <nanobind/stl/pair.h>\n'
#         header += '#include <nanobind/stl/set.h>\n'
#         header += '#include <nanobind/stl/string.h>\n'
#         header += '#include <nanobind/stl/string_view.h>\n'
#         header += '#include <nanobind/stl/wstring.h>\n'
#         header += '#include <nanobind/stl/tuple.h>\n'
#         header += '#include <nanobind/stl/shared_ptr.h>\n'
#         header += '#include <nanobind/stl/unique_ptr.h>\n'
#         header += '#include <nanobind/stl/unordered_set.h>\n'
#         header += '#include <nanobind/stl/unordered_map.h>\n'
#         header += '#include <nanobind/stl/variant.h>\n'
#         header += '#include <nanobind/stl/vector.h>\n\n'
#         header += '#include <nanobind/ndarray.h>\n\n'
#         header += f'namespace nb = nanobind;\n'
#         alpha : str = ''
#         for x in self.list:
#             alpha += '\t' + str(x) + '\n'
#         header += f"""\nvoid bindingsFor{os.path.splitext(os.path.basename(self.filenameRelative))[0].upper()}(nb::module_& m)\n{{\n{alpha}\n}}"""
#         return header     

# def main():
#     parser = argparse.ArgumentParser(prog="Nanobind Bindings Generator", 
#                                      description="Generates Nanobind bindings for C/CPP Projects")
#     parser.add_argument("--path", 
#                        required=True,
#                        help="Path to a file or folder to generate bindings for")
#     parser.add_argument("--outputDirectory",
#                         help="Output Directory",
#                         default=".")
#     parser.add_argument("--compilerOptions",
#                         help="Compiler Options to pass to clang (include dirs and such)",
#                         default="-std=c++17")
#     args = parser.parse_args()
#     if not os.path.exists(args.path):
#         parser.error("Directory or File does not exist")
#     isFolder = os.path.isdir(args.path)
#     if not isFolder:
#         fileObj = File(args.path)
#         fileObj.write_to_file()
    
def main():
    parser = argparse.ArgumentParser(prog="Nanobind Bindings Generator",
                                     description="Creates Nanobind bindings according to a YAML file")
    
    parser.add_argument("--yaml",
                        required=True,
                        help="yaml file location")
    
    args = parser.parse_args()
    
    with open(args.yaml, 'r') as f:
        yamlData = yaml.safe_load(f)
        
    print(type(yamlData['cppConfig']['cxxFlags']))