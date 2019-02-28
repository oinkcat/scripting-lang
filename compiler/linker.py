# -*- coding: utf-8 -*-
""" Module contents linker """
import sys
import re
import os
import compatibility

FILE_EXT = '.lb'

SECTION_REFS = '.refs'
SECTION_IMPORTS = '.imports'
SECTION_SHARED = '.shared'
SECTION_DATA = '.data'
SECTION_DEFS = '.defs'
SECTION_MAIN = '.entry'

OP_CALL_UDF = 'call.udf'
OP_REF_UDF = 'mk_ref.udf'
OP_LDCONST = 'load.const'
OP_LOAD = 'load'
OP_STORE = 'store'
OP_LDGLOBAL = 'load.global'
OP_STGLOBAL = 'store.global'

class CompiledModule:
    """ Compiled module """
    
    def __init__(self, name):
        self.name = name
        self.refs = []
        self.imports = []
        self.shared_vars = []
        self.const_data = []
        self.functions = []
        self.code_lines = []
        self.n_globals = 0
        
    def _transform_function_defs(self):
        """ Prepend module name before function name """
        
        for i in compatibility.num_range(0, len(self.functions)):
            func_name = self.functions[i][0]
            if '::' in func_name:
                continue
            name, args_count = func_name.split('.')
            qualified_name = '%s::%s.%s' % (self.name, name, args_count)
            self.functions[i][0] = qualified_name
            
    def _transform_code(self, code_lines, offsets, root = False):
        """ Transform function code """

        ops_ldst = { OP_LDGLOBAL, OP_STORE, OP_STGLOBAL }

        for i in compatibility.num_range(0, len(code_lines)):
            code_item = code_lines[i]
            opcode = code_item[0]
            
            if (opcode == OP_CALL_UDF) or (opcode == OP_REF_UDF):
                func_name_parts = code_item[1].split('::')
                is_bare = len(func_name_parts) == 1
                if is_bare and (func_name_parts[0] not in self.imports):
                    code_item[1] = '%s::%s' % (self.name, code_item[1])
            elif (opcode == OP_LDCONST):
                # If represents index of constant data array
                if all(c.isdigit() for c in code_item[1]):
                    idx = int(code_item[1])
                    code_item[1] = str(idx + offsets['data'])
            elif root and opcode == OP_LOAD and code_item[1][0] == '#':
                idx = int(code_item[1][1:])
                code_item[1] = '#' + str(idx + offsets['global'])
            elif opcode in ops_ldst:
                if opcode == OP_STGLOBAL or opcode == OP_LDGLOBAL or root:
                    idx = int(code_item[1])
                    code_item[1] = str(idx + offsets['global'])
        
    def transform(self, offsets):
        """ Transform module contents before merge """
        
        # Defined function names
        self._transform_function_defs()
        
        # References in functions code
        for _, code in self.functions:
            self._transform_code(code, offsets)
            
        # References in main code
        self._transform_code(self.code_lines, offsets, True)

        return offsets
        
    def save(self, out_file):
        """ Save module to stream """
        
        out_lines = list()
        
        def append(text):
            out_lines.append(text + '\n')
        
        def write_section(section_name, array):
            if len(array) > 0:
                append(section_name)
                for item in array:
                    append(item)
                    
        def write_code(code):
            for item in code:
                cmd = ' '.join(item[0:2]) if item[1] is not None \
                                          else item[0]
                if item[2] is not None:
                    append('%s ; %s' % (cmd, item[2]))
                else:
                    append(cmd)
        
        write_section(SECTION_REFS, self.refs)
        write_section(SECTION_IMPORTS, self.imports)
        write_section(SECTION_SHARED, self.shared_vars)
        write_section(SECTION_DATA, self.const_data)
        
        if len(self.functions) > 0:
            append(SECTION_DEFS)
            for name, code in self.functions:
                append(name)
                write_code(code)
                
        if len(self.code_lines) > 0:
            append(SECTION_MAIN)
            write_code(self.code_lines)
        
        out_file.writelines(out_lines)
        
    def inspect(self):
        """ Print module information """
        
        print('Module name: %s' % self.name)
        print('References: %d' % len(self.refs))
        print('Imports: %d' % len(self.imports))
        print('Shared variables: %d' % len(self.shared_vars))
        print('Constant data items: %d' % len(self.const_data))
        print('Functions count: %d' % len(self.functions))
        print('Code lines count: %d' % len(self.code_lines))
        
class CompiledModuleLoader:
    """ Loader for compiled module """
    
    def __init__(self):
        self.mod_file = None
        self.cmd_re = re.compile('^(\S+)' + \
                                 '(?:(?! ; #)\s(.+?))?' + \
                                 '(?: ; (#.+?\(\d+\)))?$')
        self.line = None
        
    def next_line(self):
        unicode_line = compatibility.gen_next(self.mod_file).strip()
        self.line = compatibility.unicode_to_str(unicode_line)

    def split_cmd_parts(self):
        
        op, m_arg, m_src_info = self.cmd_re.findall(self.line)[0]
        arg = m_arg if len(m_arg) > 0 else None
        src_info = m_src_info if len(m_src_info) > 0 else None

        return [op, arg, src_info]
    
    def read_section_lines(self, destination):
        """ Read text lines within section into destination array """
        
        while True:
            self.next_line()
            if self.line.startswith('.'):
                return
            destination.append(self.line)
        
    def read_functions(self, module):
        """ Read function definitions """
        
        func_name_regex = re.compile('^.+\.[0-9]+:$')
        func_info = None
        
        while True:
            self.next_line()

            if func_name_regex.match(self.line) is not None:
                func_info = [self.line, list()]
                module.functions.append(func_info)
            elif self.line.startswith('.'):
                return
            else:
                func_info[1].append(self.split_cmd_parts())
            
    def read_code(self, module):
        """ Read main code """
    
        while True:
            self.next_line()
            op_parts = self.split_cmd_parts()
            if op_parts[0] == OP_STORE:
                var_num = int(op_parts[1]) + 1
                if var_num > module.n_globals:
                    module.n_globals = var_num
            module.code_lines.append(op_parts)
    
    def read_sections(self, module):
        """ Load module contents """
        
        self.next_line()
        
        while True:
            if self.line == SECTION_REFS:
                self.read_section_lines(module.refs)
            elif self.line == SECTION_IMPORTS:
                self.read_section_lines(module.imports)
            elif self.line == SECTION_SHARED:
                self.read_section_lines(module.shared_vars)
                self.n_globals = len(self.shared_vars)
            elif self.line == SECTION_DATA:
                self.read_section_lines(module.const_data)
            elif self.line == SECTION_DEFS:
                self.read_functions(module)
            elif self.line == SECTION_MAIN:
                self.read_code(module)
            else:
                raise Exception('Invalid section name: %s!' % self.line)

    def load(self, name):
        """ Load compiled module """
        
        with compatibility.open_utf8(name) as mod_file:
            self.mod_file = mod_file
            mod_name = os.path.basename(name)[0:-3]
            loaded_module = CompiledModule(mod_name)
            try:
                self.read_sections(loaded_module)
            except StopIteration:
                pass
                
            return loaded_module
            
class Merger:
    """ Merges two modules """
    
    def append_module_contents(self, dest, src):
        """ Append contents of source module to destination """
        
        # Native module references
        dest.refs.extend(src.refs)
        dest.refs = list(set(dest.refs))
        
        # Shared variables
        dest.shared_vars.extend(src.shared_vars)
            
        # Constant data
        dest.const_data.extend(src.const_data)
            
        # Function definitions
        dest.functions.extend(src.functions)
            
        # Code lines
        dest.code_lines.extend(src.code_lines)
    
    def merge(self, accum, ref):
        """ Merge two modules """

        # Transform referenced module
        offsets = {
            'global': 0,
            'data': 0
        }
        ref.transform(offsets)

        merged_module = CompiledModule('result')
        self.append_module_contents(merged_module, ref)

        # Transform target module
        offsets['global'] = ref.n_globals
        offsets['data'] = len(ref.const_data)
        accum.transform(offsets)

        self.append_module_contents(merged_module, accum)
        merged_module.n_globals = accum.n_globals + ref.n_globals
        
        return merged_module
        
class Linker:
    """ Link module with all referenced modules """

    def __init__(self, module, resolver):
        self.main_mod = module
        self.mods_resolver = resolver
        self.all_imports = set()
        self.merger = Merger()
        
    def _get_full_name(self, mod_name):
        """ Get full name of module file """
        return os.path.join(self.base_dir, mod_name + FILE_EXT)
    
    def merge_imports(self, target_mod):
        """ Link module with it's imports """
        
        result_mod = target_mod
        
        for ref_mod_name in target_mod.imports:
            if ref_mod_name in self.all_imports:
                continue
                
            ref_mod = self.mods_resolver.get_dependency(ref_mod_name)
            self.all_imports.add(ref_mod.name)
            ref_mod = self.merge_imports(ref_mod)
            result_mod = self.merger.merge(result_mod, ref_mod)
            
        return result_mod
        
    def link(self):
        """ Link all referenced modules """
        
        return self.merge_imports(self.main_mod)