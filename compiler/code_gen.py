""" Code generator """
import os
from ast import *

class Scope:
    """ Global or function scope """
    
    def __init__(self, name):
        self.name = name
        self.variables = dict()
        self.global_refs = set()
        
class CodeGen:
    """ Code generator with some optimizations """
    
    BUILTIN_MODULE_NAME = '$builtin'

    DEFS_FILEEXT = '.ld'

    # Literal type
    LIT_NUMBER = 0
    LIT_STRING = 1
    
    # External definitions type
    EXT_CONST = 'const'
    EXT_FUNC = 'func'
    
    # Section identifiers
    SECTION_REF = '.ref'
    SECTION_IMPORT = '.import'
    SECTION_SHARED = '.shared'
    SECTION_DATA = '.data'
    SECTION_FUNCS = '.defs'
    SECTION_ENTRY = '.entry'

    COMMON_OPS = { 
        '+': 'add', '-': 'sub', 
        '*': 'mul', '/': 'div', '%': 'mod',
        '<': 'lt', '<=': 'le', '>': 'gt', '>=': 'ge',
        '==': 'eq', '!=': 'ne',
        '&': 'concat'
    }
    
    JMP_OPCODES = {
        '<': 'jmplt', '<=': 'jmple',
        '>': 'jmpgt', '>=': 'jmpge',
        '==': 'jmpeq', '!=': 'jmpne'
    }
    
    CMP_INVERSE = {
        '<': '>=', '>': '<=',
        '<=': '>', '>=': '<',
        '==': '!=', '!=': '=='
    }
    
    def __init__(self, root_node, out_file):
        self.ast = root_node
        self.output_file = out_file
        self.scopes = []
        self.defined_funcs = set()
        self.functions_refs = set()
        # Indexes of opcodes with global variables
        self.global_var_gen_idxs = []
        self.generated = []
        # Module contents
        self.shared_vars = []
        self.imports = []
        self.native_refs = dict()
        self.const_data = []

        self.entry_node = None
        self.last_op = None
        self.last_jmp_id = 0
        
    def load_module_defs(self, mod_name):
        """ Load module function definitions """

        curdir_path = os.path.dirname(os.path.realpath(__file__))
        defs_path = curdir_path + '/../defs/'
        mod_filename = defs_path + mod_name + CodeGen.DEFS_FILEEXT
        defs_file = open(mod_filename)

        contents = dict()
        
        for def_item in defs_file.xreadlines():
            name = def_item.strip()
            if len(name) > 0 and name[0] != '#':
                if '.' in name:
                    func_name = name[0:name.find('.')]
                    contents[func_name] = CodeGen.EXT_FUNC
                else:
                    contents[name] = CodeGen.EXT_CONST
                
        self.native_refs[mod_name] = contents
        defs_file.close()

    def is_native_func(self, module_name, name):
        """ Check if function with given name is native """

        if module_name in self.native_refs:
            module_refs = self.native_refs[module_name]
            return module_refs.get(name) == CodeGen.EXT_FUNC
        else:
            return False

    def qualified_name(self, mod_name, item_name):
        """ Get name prepended with module name """

        return mod_name + '::' + item_name
        
    def get_scope(self):
        """ Get current scope name """
        
        return self.scopes[len(self.scopes) - 1]
        
    def put_scope_var(self, var_name):
        """ Put variable in current scope """
        
        vars = self.get_scope().variables
        if vars.has_key(var_name):
            return vars[var_name]
        elif var_name in self.get_scope().global_refs:
            # Index needs to be resolved later
            return None
        else:
            var_idx = len(vars)
            vars[var_name] = var_idx
            return var_idx
        
    def get_scope_var(self, var_name):
        """ Get index of variable from current scope """
        
        vars = self.get_scope().variables
        if vars.has_key(var_name):
            return vars[var_name]
        else:
            # Variable not found in current scope
            # Check if global, otherwise fail
            scope = self.get_scope()
            if var_name in scope.global_refs:
                # Index need to be resolved later
                return None
            else:
                msg = 'Variable or constant %s not found in scope %s!' \
                      % (var_name, self.get_scope().name)
                raise Exception(msg)
            
    def is_const_array(self, node):
        """ Check if array contains only const values """
        
        for elem in node.elements:
            if not isinstance(elem, NumberNode) and \
               not isinstance(elem, StringNode):
                return False
                
        return len(node.elements) > 0
        
    def add_global_var_ref(self, op, name):
        """ Add reference to global variable """
        
        self.global_var_gen_idxs.append(len(self.generated))
        self.emit('!%s.global' % op, name)
        
    def resolve_global_vars(self):
        """ Resolve global variable names to it's indexes """
        
        global_scope = self.scopes[0]
        
        for gen_idx in self.global_var_gen_idxs:
            op, var_name = self.generated[gen_idx].split()
            var_idx = global_scope.variables[var_name]
            resolved_opcode = '%s %d' % (op[1:], var_idx)
            self.generated[gen_idx] = resolved_opcode

    def check_function_refs(self):
        """ Check referenced function names """

        undefined = self.functions_refs.difference(self.defined_funcs)

        if len(undefined) > 0:
            func_names = ', '.join(undefined)
            raise Exception('Undefined functions: ' + func_names)
        
    def generate(self):
        """ Start code generation """

        if self.ast is None or len(self.ast.statements) == 0:
            raise Exception('No AST specified!')
        
        # Find function definitions section
        root_statements = self.ast.statements
        for node in root_statements:
            if isinstance(node, FuncNode):
                self.emit(CodeGen.SECTION_FUNCS)
                break
            elif not node.is_directive():
                break
            
        # Find entry point
        for node in root_statements:
            if (not isinstance(node, FuncNode)) and \
               (not node.is_directive()):
                self.entry_node = node
                break
        
        # Traverse AST
        self.scopes.append(Scope('global'))
        self.ast.accept(self)
        
        # Resolve global variable indexes
        if len(self.global_var_gen_idxs) > 0:
            self.resolve_global_vars()

        # Check function references
        self.check_function_refs()
        
        # Write generated code to output file
        self.write_out()

    def new_jmp_id(self):
        self.last_jmp_id += 1
        return self.last_jmp_id

    def emit(self, op, args_str = None):
        """ Emit opcode """
        
        self.last_op = op
        output = op
        if args_str != None:
            output += ' ' + args_str
        
        self.generated.append(output)
        
    def emit_if_cond(self, cond_expr, has_else, branch_label):
        """ Emit if statement/expression's condition """
        
        if isinstance(cond_expr, CMPNode):
            cond_expr.l.accept(self)
            cond_expr.r.accept(self)
            cmp_op = cond_expr.op if has_else \
                     else CodeGen.CMP_INVERSE[cond_expr.op]
            jmp_op = CodeGen.JMP_OPCODES[cmp_op]
            self.emit(jmp_op, branch_label)
        else:
            cond_expr.accept(self)
            cmp_arg = 'true' if has_else else 'false'
            self.emit('load.const', cmp_arg)
            self.emit('jmpeq', branch_label)

    def visit_binary_expr(self, node):
        """ Visit binary expression node """

        node.l.accept(self)
        node.r.accept(self)
        if isinstance(node, LogicNode):
            self.emit(node.op)
        else:
            self.emit(CodeGen.COMMON_OPS[node.op])

    def visit_simple_literal(self, node, type):
        """ Visit number or string node """

        if type == CodeGen.LIT_NUMBER:
            self.emit('load', str(node.value))
        else:
            self.emit('load', node.value)

    def visit_variable(self, node):
        """ Visit variable node """
        
        builtin_refs = self.native_refs[CodeGen.BUILTIN_MODULE_NAME]
        if node.name in builtin_refs:
            self.emit('load.const', node.name)
        else:
            var_idx = self.get_scope_var(node.name)
            if var_idx is not None:
                self.emit('load', '#' + str(var_idx))
            else:
                self.add_global_var_ref('load', node.name)

    def visit_function_call(self, node):
        """ Visit function call node """
        
        # Arguments
        for arg_expr in node.call_args:
            arg_expr.accept(self)

        # Module name
        if isinstance(node.call_expr,IdentifierNode):
            mod_name = CodeGen.BUILTIN_MODULE_NAME
            func_name = node.call_expr.name
        elif isinstance(node.call_expr, ItemGetNode):
            mod_name = node.call_expr.array_expr.name
            func_name = node.call_expr.index_expr.value[1:-1]

        if self.is_native_func(mod_name, func_name):
            # External function
            self.emit('call', self.qualified_name(mod_name, func_name))
        else:
            # User defined function
            if isinstance(node.call_expr, IdentifierNode):
                self.functions_refs.add(func_name)
                self.emit('invoke', func_name)
            else:
                raise Exception("User defined modules not yet implemented!")

    def visit_math_inv(self, node):
        """ Visit math inversion node """
        
        node.expr.accept(self)
        self.emit('load -1')
        self.emit('mul')

    def visit_logic_inv(self, node):
        """ Visit logic inversion node """

        node.expr.accept(self)
        self.emit('not')

    def visit_block(self, node):
        """ Visit block node """
        
        for stmt in node.statements:
            stmt.accept(self)

    def visit_assign(self, node):
        """ Visit variable assign node """

        node.expr.accept(self)
        var_idx = self.put_scope_var(node.name)
        if var_idx is not None:
            self.emit('store', str(var_idx))
        else:
            self.add_global_var_ref('store', node.name)

    def visit_if_expr(self, node):
        """ Visit if expression node """
        
        id = self.new_jmp_id()
        end_label = 'IFE_END_%d' % id

        true_label = 'IFE_TB_%d' % id
        self.emit_if_cond(node.cond_expr, True, true_label)
        node.false_expr.accept(self)
        self.emit('jmp', end_label)
        self.emit(true_label + ':')
        node.true_expr.accept(self)
        self.emit(end_label + ':')

    def visit_if_statement(self, node):
        """ Visit if statement node """

        id = self.new_jmp_id()
        end_label = 'IF_END_%d' % id

        if node.else_branch is not None:
            # Conditions
            for idx, cond in enumerate(node.cond_branches):
                branch_label = 'IF_C_%d_%d' % (id, idx + 1)
                self.emit_if_cond(cond[0], True, branch_label)

            # Branches
            node.else_branch.accept(self)
            self.emit('jmp', end_label)
            for idx, cond in enumerate(node.cond_branches):
                self.emit('IF_C_%d_%d:' % (id, idx + 1))
                cond[1].accept(self)
                if idx < len(node.cond_branches) - 1:
                    self.emit('jmp', end_label)
        else:
            # Conditions and branches
            for idx, cond in enumerate(node.cond_branches):
                jmp_label = 'IF_C_%d_%d' % (id, idx + 2) \
                                if idx < len(node.cond_branches) - 1 \
                                else end_label
                self.emit_if_cond(cond[0], False, jmp_label)
                cond[1].accept(self)
                if jmp_label != end_label:
                    self.emit('jmp', end_label)
                    self.emit(jmp_label + ':')
        # Exit label
        self.emit(end_label + ':')

    def visit_for_while_loop(self, node):
        """ Visit for (while) loop node """

        id = self.new_jmp_id()
        true_label = 'FOR_LOOP_%d' % id
        self.emit('FOR_COND_%d:' % id)
        self.emit_if_cond(node.cond_expr, True, true_label)
        self.emit('jmp', 'FOR_END_%d' % id)
        self.emit(true_label + ':')
        node.loop_block.accept(self)
        self.emit('jmp', 'FOR_COND_%d' % id)
        self.emit('FOR_END_%d:' % id)
        
    def visit_for_each_loop(self, node):
        """ Visit for (enumerative) loop node """
        
        id = self.new_jmp_id()
        node.iter_expr.accept(self)
        self.emit('call', '_iter_create$')
        self.emit('FOR_COND_%d:' % id)
        self.emit('dup')
        self.emit('call', '_iter_hasnext$')
        self.emit('load.const', 'true')
        self.emit('jmpne', 'FOR_END_%d' % id)
        self.emit('dup')
        self.emit('call', '_iter_next$')
        var_idx = self.put_scope_var(node.var_name)
        self.emit('store', str(var_idx))
        node.loop_block.accept(self)
        self.emit('jmp', 'FOR_COND_%d' % id)
        self.emit('FOR_END_%d:' % id)
        self.emit('unload')

    def visit_func_def(self, node):
        """ Visit function definition node """
        
        self.defined_funcs.add(node.name)
        self.scopes.append(Scope(node.name))
        for param_name in node.param_list:
            self.put_scope_var(param_name)
        num_params = len(node.param_list)
        self.emit('%s.%d:' % (node.name, num_params))
        node.func_block.accept(self)
        if not self.last_op == 'ret':
            self.emit('ret')
        self.scopes.pop()

    def visit_return(self, node):
        """ Visit return node """
        
        if node.result is not None:
            node.result.accept(self)
        self.emit('ret')
        
    def visit_emit(self, node):
        """ Visit emit result node """

        node.value.accept(self)
        if node.name is not None:
            self.emit('emit', '"%s"' % node.name)
        else:
            self.emit('emit')

    def visit_array_def(self, node):
        """ Visit array definition node """

        num_elems = len(node.elements)
        if node.is_hash:
            for key, elem in node.elements:
                self.emit('load', '"%s"' % key)
                elem.accept(self)
            self.emit('mk_hash', str(num_elems))
        else:
            if self.is_const_array(node):
                # Array with only constants
                self.const_data.append(node)
                array_idx = len(self.const_data) - 1
                self.emit('load.const', str(array_idx))
            else:
                # Array with expressions/variables/mixed
                for elem in node.elements:
                    elem.accept(self)
                self.emit('mk_array', str(num_elems))

    def visit_get(self, node):
        """ Visit compound item's member access node """

        module_found = False
        if isinstance(node.array_expr, IdentifierNode):
            mod_name = node.array_expr.name
            module_found = mod_name in self.native_refs
        
        if module_found:
            module_contents = self.native_refs[mod_name]
            const_name = node.index_expr.value[1:-1]
            if const_name in module_contents:
                full_name = self.qualified_name(mod_name, const_name)
                self.emit('load.const', full_name)
            else:
                args = (const_name, mod_name)
                raise('Constant %s not found in module %s!' % args)
        else:
            node.array_expr.accept(self)
            node.index_expr.accept(self)
            self.emit('get')

    def visit_set(self, node):
        """ Visit compound item's member value setup """

        node.elem_expr.accept(self)
        node.array_expr.accept(self)
        node.index_expr.accept(self)

        # Optionally perform math (?) operation
        if node.op is None:
            self.emit('set')
        else:
            self.emit('set.op', CodeGen.COMMON_OPS[node.op])

    def visit_bind_extern_var(self, node):
        """ Visit global/shared with host variable binding node """

        scope = self.get_scope()
        if scope.name == 'global':
            # A variable shared with host
            for var_name in node.variables:
                self.shared_vars.append(var_name)
                self.put_scope_var(var_name)
        else:
            # A global variable
            scope.global_refs.update(node.variables)

    def visit_add_module_ref(self, node):
        """ Visit module reference node """

        if node.native:
            for mod_name in node.modules:
                if mod_name not in self.native_refs:
                    self.load_module_defs(mod_name)
        else:
            raise NotImplementedError('Only native modules is implemented!')

    def visit(self, node):
        """ Visit AST node and generate code """
        
        # Emit entry point section marker
        if node == self.entry_node:
            self.emit(CodeGen.SECTION_ENTRY)
        
        if isinstance(node, MathNode) or \
           isinstance(node, CMPNode) or \
           isinstance(node, LogicNode) or \
           isinstance(node, StringOpNode):
            # Binary expression
            self.visit_binary_expr(node)
        elif isinstance(node, NumberNode):
            # Integer/float number
            self.visit_simple_literal(node, CodeGen.LIT_NUMBER)
        elif isinstance(node, StringNode):
            # Character string
            self.visit_simple_literal(node, CodeGen.LIT_STRING)
        elif isinstance(node, IdentifierNode):
            # Variable identifier
            self.visit_variable(node)
        elif isinstance(node, InvokeNode):
            # Function invocation
            self.visit_function_call(node)
        elif isinstance(node, MinusNode):
            # Math inversion
            self.visit_math_inv(node)
        elif isinstance(node, NegateNode):
            # NOT expression
            self.visit_logic_inv(node)
        elif isinstance(node, BlockNode):
            # Sequence of statements
            self.visit_block(node)
        elif isinstance(node, AssignNode):
            # Assignment to variable
            self.visit_assign(node)
        elif isinstance(node, CondNode):
            # If expression
            self.visit_if_expr(node)
        elif isinstance(node, IfNode):
            # If statement
            self.visit_if_statement(node)
        elif isinstance(node, ForWhileNode):
            # While loop statement
            self.visit_for_while_loop(node)
        elif isinstance(node, ForEachNode):
            # Iterative loop statement
            self.visit_for_each_loop(node)
        elif isinstance(node, FuncNode):
            # Function definition
            self.visit_func_def(node)
        elif isinstance(node, ReturnNode):
            # Return statement
            self.visit_return(node)
        elif isinstance(node, EmitNode):
            # Emit result statement
            self.visit_emit(node)
        elif isinstance(node, ArrayNode):
            # Array/hash literal
            self.visit_array_def(node)
        elif isinstance(node, ItemGetNode):
            # Array indexing
            self.visit_get(node)
        elif isinstance(node, ItemSetNode):
            # Array element value setup
            self.visit_set(node)
        elif isinstance(node, UseVariableNode):
            # Directive for using external variable(s)
            self.visit_bind_extern_var(node)
        elif isinstance(node, ImportModuleNode):
            self.visit_add_module_ref(node)
        else:
            raise Exception('Unknown node type (%s)!' % type(node))
            
    def write_out(self):
        """ Output generated code to file """
        
        def out_line(line):
            self.output_file.write(line + "\n")
            
        def out_const_array(array):
            elem_values = [str(elem.value) for elem in array.elements]
            out_line(' '.join(elem_values))

        # Native module references section
        if len(self.native_refs) > 0:
            out_line(CodeGen.SECTION_REF)
            for mod_name in self.native_refs:
                out_line(mod_name)
            
        # Shared variables section
        if len(self.shared_vars) > 0:
            out_line(CodeGen.SECTION_SHARED)
            for var_name in self.shared_vars:
                out_line(var_name)
        
        # Constant data section
        if len(self.const_data) > 0:
            out_line(CodeGen.SECTION_DATA)
            for data_item in self.const_data:
                if isinstance(data_item, ArrayNode):
                    out_const_array(data_item)
                else:
                    raise Exception('Only constant array supported as data!')
            
        for code_item in self.generated:
            out_line(code_item)