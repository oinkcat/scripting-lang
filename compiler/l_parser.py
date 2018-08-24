""" Parser syntax rules """
from tokenizer import *
from ast import *

class InvalidToken(Exception):
    """ Invalid token occured """
    
    def __init__(self, src):
        tok_name = get_token_name(src.t_type)
        args = (tok_name, src.t_val, src.line_number, src.line)
        msg = 'Invalid token: %s, %s\nLine: %d, %s' % args
        Exception.__init__(self, msg)

class Parser:
    """ Language statements parser """

    # Block types
    B_OUTER = 0
    B_FUNC = 1
    B_STMT = 2

    def __init__(self, tokenizer):
        self.stack = []
        self.scope_names = []
        self.tokens_source = tokenizer
        self.root_node = None
        self.auto_id = 0

    def get_next_id(self):
        """ Return new generated identifier """

        self.auto_id += 1
        return self.auto_id
        
    def require_cr(self, src):
        """ Require occurence of EOL token """

        delimiters = { T_EOL, T_EOF }
        if src.t_type not in delimiters:
            raise InvalidToken(src)
        src.next()
        
    def strip_cr(self, src):
        """ Skip EOL tokens """

        while src.t_type == T_EOL:
            src.next()

    def append_function(self, func):
        """ Append new function definition node """
        
        pos = 0
        for node in self.root_node.statements:
            if not node.is_directive():
                break
            pos += 1
        self.root_node.statements.insert(pos, func)
        
    def parse_to_ast(self):
        """ Parse all tokens """
        
        return self.parse_block(self.tokens_source, Parser.B_OUTER)
        
    def parse_factor(self, src):
        """ Atom or subexpression """

        src.next()
        
        # Value can be inverted
        inverted = src.t_type == T_ADD and src.t_val == '-'
        if inverted:
            src.next()        
        
        result = None
        if src.t_type == T_NUMBER:
            result = NumberNode(src, src.t_val)
        elif src.t_type == T_STRING:
            if inverted:
                raise InvalidToken(src)
            result = StringNode(src, src.t_val)
        elif src.t_type == T_IDENT:
            # Variable/array reference or function call
            result = self.parse_access(src)
        elif src.t_type == T_IF:
            # If expression
            src.next()
            result = self.parse_cond_expr(src)
        elif src.t_type == T_LBR:
            self.parse_expr(src)
            if src.t_type != T_RBR:
                raise InvalidToken(src)
            result = self.stack.pop()
        elif src.t_type == T_LSBR:
            if inverted:
                raise InvalidToken(src)
            result = self.parse_array(src)
        elif src.t_type == T_LCBR:
            if inverted:
                raise InvalidToken(src)
            result = self.parse_hash_array(src)
        else:
            raise InvalidToken(src)
            
        if inverted:
            if isinstance(result, NumberNode):
                result.value *= -1
                self.stack.append(result)
            else:
                self.stack.append(MinusNode(src, result))
        else:
            self.stack.append(result)
        
    def parse_morefactors(self, src):
        """ Operators priority: 1 """
        
        src.next()
        if src.t_type == T_MUL:
            op = src.t_val
            self.parse_factor(src)
            f2 = self.stack.pop()
            f1 = self.stack.pop()
            f_expr = MathNode(src, f1, f2, op)
            self.stack.append(f_expr)
            self.parse_morefactors(src)
        
    def parse_moreterms(self, src):
        """ Operators priority: 2 """

        if src.t_type == T_ADD:
            op = src.t_val
            self.parse_term(src)
            t2 = self.stack.pop()
            t1 = self.stack.pop()
            t_expr = MathNode(src, t1, t2, op)
            self.stack.append(t_expr)
            self.parse_moreterms(src)

    def parse_term(self, src):
        """ Addition and subtraction operators """
    
        self.parse_factor(src)
        self.parse_morefactors(src)

    def parse_morecmp(self, src):
        """ Operators priority: 3 """
        
        if src.t_type == T_CMP:
            op = src.t_val
            self.parse_cmp(src)
            c2 = self.stack.pop()
            c1 = self.stack.pop()
            c_expr = CMPNode(src, c1, c2, op)
            self.stack.append(c_expr)
            self.parse_morecmp(src)
        
    def parse_cmp(self, src):
        """ Comparsion operators """
    
        self.parse_term(src)
        self.parse_moreterms(src)

    def parse_moreconds(self, src):
        """ Operators priority: 4 """
        
        if src.t_type == T_LOGIC:
            op = src.t_val
            self.parse_cond(src)
            l2 = self.stack.pop()
            l1 = self.stack.pop()
            l_expr = LogicNode(src, l1, l2, op)
            self.stack.append(l_expr)
            self.parse_moreconds(src)

    def parse_cond(self, src):
        """ Logic operators """
        
        # String may take multiple lines
        can_wrap_line = src.t_type == T_CONCAT

        negated = False
        src.next()

        if can_wrap_line:
            self.strip_cr(src)

        if src.t_type == T_NOT:
            negated = True
        else:
            src.hold()

        self.parse_cmp(src)
        self.parse_morecmp(src)
        
        if negated:
            expr = self.stack.pop()
            self.stack.append(NegateNode(src, expr))
        
    def parse_moreconcats(self, src):
        """ Operators priority: 5 """
        
        if src.t_type == T_CONCAT:
            self.parse_concat(src)
            sc2 = self.stack.pop()
            sc1 = self.stack.pop()
            # Optimize concatenation of two strings
            if isinstance(sc1, StringNode) and isinstance(sc2, StringNode):
                left_part = sc1.value[0:-1]
                right_part = sc2.value[1:]
                concatenated = StringNode(src, left_part + right_part)
                self.stack.append(concatenated)
            else:
                sc_expr = StringOpNode(src, sc1, sc2)
                self.stack.append(sc_expr)
            self.parse_moreconcats(src)

    def parse_concat(self, src):
        """ String concatenation """
        
        self.parse_cond(src)
        self.parse_moreconds(src)
            
    def parse_expr(self, src):
        """ Expression/subexpression """
        
        src.next()
        if src.t_type == T_FUNCREF:
            ref_expr = self.parse_function_ref(src)
            self.stack.append(ref_expr)
        elif src.t_type == T_NEW:
            obj_expr = self.parse_obj(src)
            self.stack.append(obj_expr)
        elif src.t_type == T_FUNC:
            # Add function declaration with auto-generated name
            src.next()
            lambda_expr = self.parse_func(src, True)
            self.append_function(lambda_expr)
            lambda_ref = FunctionRefNode(src, lambda_expr.name)
            self.stack.append(lambda_ref)
        else:
            src.hold()
            self.parse_concat(src)
            self.parse_moreconcats(src)

    def parse_function_ref(self, src):
        """ Reference to function """

        src.next()
        if src.t_type != T_IDENT:
            raise InvalidToken(src)

        name_part = src.t_val
        src.next()

        if src.t_type == T_DOT:
            src.next()
            if src.t_type != T_IDENT:
                raise InvalidToken()
            func_name = src.t_val
            src.next()
            return FunctionRefNode(src, func_name, name_part)
        else:
            return FunctionRefNode(src, name_part)

    def parse_obj(self, src):
        """ Parse object constructor """

        src.next()
        if src.t_type != T_LCBR:
            raise InvalidToken(src)

        hash = self.parse_hash_array(src)
        src.next()

        return NewObjNode(src, hash)
        
    def parse_arglist(self, src):
        """ Function call arguments list """
        
        delims = { T_COMMA, T_RBR }
        arg_exprs = []
        
        src.next()
        while src.t_type != T_RBR:
            # If first time
            if len(arg_exprs) == 0:
                src.hold()
            self.parse_expr(src)
            arg_exprs.append(self.stack.pop())
            if src.t_type not in delims:
                raise InvalidToken(src)
            
        return arg_exprs

    def parse_cond_expr(self, src):
        """ If expression """
        
        if src.t_type != T_LBR:
            raise InvalidToken(src)
        # Condition
        self.parse_expr(src)
        cond = self.stack.pop()
        if src.t_type != T_COMMA:
            raise InvalidToken(src)
        # True branch expression
        self.parse_expr(src)
        true_expr = self.stack.pop()
        if src.t_type != T_COMMA:
            raise InvalidToken(src)
        # False branch expression
        self.parse_expr(src)
        false_expr = self.stack.pop()
        if src.t_type != T_RBR:
            raise InvalidToken(src)
        
        return CondNode(src, cond, true_expr, false_expr)

    def parse_if_stmt(self, src):
        """ If statement """
        
        # Conditions and blocks
        conds_and_blocks = []

        has_condition = True
        while has_condition:
            # Condition expression
            self.parse_expr(src)
            cond = self.stack.pop()
            self.require_cr(src)
            # Associated block
            branch = self.parse_block(src, Parser.B_STMT)

            conds_and_blocks.append((cond, branch))

            # Next alternative (else if)
            src.next()
            has_condition = src.t_type == T_ELSEIF

        # Else block (optional)
        f_branch = None
        if src.t_type == T_ELSE:
            src.next()
            self.require_cr(src)
            f_branch = self.parse_block(src, Parser.B_STMT)
            src.next()
        
        if src.t_type != T_END:
            raise InvalidToken(src)
        src.next()
            
        return IfNode(src, conds_and_blocks, f_branch)

    def parse_for(self, src):
        """ For loop (loops?) """
        
        # Condition/expression
        self.parse_expr(src)
        expr = self.stack.pop()
        
        # Variable to hold each element
        iter_var = None
        if src.t_type == T_AS:
            src.next()
            if src.t_type != T_IDENT:
                raise InvalidToken(src)
            iter_var = src.t_val
            src.next()
        
        self.require_cr(src)
        
        # Looping statements block
        loop = self.parse_block(src, Parser.B_STMT)
        src.next()
        
        if src.t_type != T_END:
            raise InvalidToken(src)
        src.next()
        
        if iter_var is None:
            return ForWhileNode(src, expr, loop)
        else:
            return ForEachNode(src, expr, iter_var, loop)

    def parse_paramlist(self, src):
        """ Function parameters list """
        
        delims = { T_COMMA, T_RBR }
        param_names = []
        
        while src.t_type != T_RBR:
            if src.t_type == T_IDENT:
                param_names.append(src.t_val)
            src.next()
            
            if src.t_type not in delims:
                raise InvalidToken(src)
            elif src.t_type == T_COMMA:
                src.next()
                
        return param_names

    def parse_func(self, src, is_lambda=False):
        """ Function definition """
        
        # Name
        if not is_lambda:
            if src.t_type != T_IDENT:
                raise InvalidToken(src)
            id = src.t_val
            src.next()
        else:
            id = '$lambda_%s' % str(self.get_next_id())

        # Push scope name
        self.scope_names.append(id)
        
        # Parameters list
        if src.t_type != T_LBR:
            raise InvalidToken(src)
        src.next()
        
        params = self.parse_paramlist(src)
        src.next()

        # Parent scope variables using
        uses = None
        if src.t_type == T_USE:
            uses = self.parse_use(src)

        # Short or full body declaration syntax
        if src.t_type == T_ASSIGN:
            # One-line body
            src.next()
            if src.t_val == '>': # =>
                src.next()
                body_block = BlockNode(src)
                body_block.statements.append(self.parse_stmt(src))
            else:
                raise InvalidToken(src)
        else:
            # Multi-line body
            self.require_cr(src)
        
            # Function body
            body_block = self.parse_block(src, Parser.B_FUNC)
            src.next()
            if src.t_type != T_END:
                raise InvalidToken(src)
            src.next()

        # Pop scope name
        self.scope_names.pop()

        # Add parent variable references from function declaration
        if uses is not None:
            body_block.statements.insert(0, uses)
        
        # Definition scope
        def_scope = self.scope_names[-1] if len(self.scope_names) > 0 else None

        return FuncNode(src, id, params, body_block, def_scope)

    def parse_array(self, src):
        """ Array literal """
        
        elems = []
        
        while src.t_type != T_RSBR:
            src.next()
            self.strip_cr(src)
            if src.t_type != T_RSBR:
                src.hold()
                self.parse_expr(src)
                elems.append(self.stack.pop())
                self.strip_cr(src)
                if src.t_type != T_COMMA and src.t_type != T_RSBR:
                    raise InvalidToken(src)
        
        return ArrayNode(src, elems, False)
        
    def parse_hash_array(self, src):
        """ Hashed array literal """
        
        elems = []
        
        while src.t_type != T_RCBR:
            src.next()
            self.strip_cr(src)
            if src.t_type != T_RCBR:
                # Hash key
                if src.t_type != T_HASHKEY:
                    raise InvalidToken(src)
                key = src.t_val[0:-1]
                # Hash element
                self.parse_expr(src)
                elems.append((key, self.stack.pop()))
                self.strip_cr(src)
                if src.t_type != T_COMMA and src.t_type != T_RCBR:
                    raise InvalidToken(src)
        
        return ArrayNode(src, elems, True)

    def parse_access(self, src, assignment = False):
        """ Parse compound element access """

        delims = {T_LSBR, T_DOT}
        # Deny function call in assignments
        if not assignment:
            delims.add(T_LBR)

        access_expr = IdentifierNode(src, src.t_val)
        src.next()

        while src.t_type in delims:
            index_expr = None
            if src.t_type == T_LSBR:
                # Array/hash indexing
                self.parse_expr(src)
                index_expr = self.stack.pop()
                if src.t_type != T_RSBR:
                    raise InvalidToken(src)
                access_expr = ItemGetNode(src, access_expr, index_expr)
            elif src.t_type == T_DOT:
                # Hash element access
                src.next()
                if src.t_type != T_IDENT:
                    raise InvalidToken(src)
                index_expr = StringNode(src, '"%s"' % src.t_val)
                access_expr = ItemGetNode(src, access_expr, index_expr)
            else:
                # Invocation
                args = self.parse_arglist(src)
                access_expr = InvokeNode(src, access_expr, args)
            src.next()

        src.hold()

        return access_expr

    def parse_assign(self, src, target):
        """ Parse assignment to variable/array/hash """

        if src.t_type == T_ASSIGN or src.t_type == T_MATHASSIGN:
            # Assignment with math operation
            op = src.t_val[0] if src.t_type == T_MATHASSIGN else None

            self.parse_expr(src)
            expr = self.stack.pop()

            if isinstance(target, IdentifierNode):
                if op is not None:
                    # Perform math operation first
                    ident = IdentifierNode(src, target.name)
                    expr = MathNode(src, ident, expr, op)

                return AssignNode(src, target.name, expr)
            else:
                array_expr = target.array_expr
                idx_expr = target.index_expr
                return ItemSetNode(src, array_expr, idx_expr, expr, op)

    def parse_stmt(self, src):
        """ Block level statement """
        
        if src.t_type == T_IDENT:
            # Assignment or function call
            target_expr = self.parse_access(src, True)
            src.next()
            if src.t_type == T_ASSIGN or src.t_type == T_MATHASSIGN:
                return self.parse_assign(src, target_expr)
            elif src.t_type == T_LBR:
                args = self.parse_arglist(src)
                src.next()
                return InvokeNode(src, target_expr, args)
            else:
                raise InvalidToken(src)
        elif src.t_type == T_IF:
            # If statement
            return self.parse_if_stmt(src)
        elif src.t_type == T_FOR:
            # Loop
            return self.parse_for(src)
        elif src.t_type == T_BREAK or src.t_type == T_CONTINUE:
            # Loop flow control
            is_continue = src.t_type == T_CONTINUE
            src.next()
            loop_depth = 1
            if src.t_type == T_NUMBER:
                loop_depth = int(src.t_val)
                src.next()
            else:
                src.hold()
            return LoopControlNode(src, is_continue, loop_depth)
        elif src.t_type == T_RETURN:
            # Return from function
            src.next()
            value = None
            if src.t_type != T_EOL:
                src.hold()
                self.parse_expr(src)
                value = self.stack.pop()
            return ReturnNode(src, value)
        elif src.t_type == T_EMIT:
            # Yield result to host
            self.parse_expr(src)
            value = self.stack.pop()
            key = None
            if src.t_type == T_AS:
                src.next()
                if src.t_type != T_IDENT:
                    raise InvalidToken(src)
                key = src.t_val
                src.next()
            return EmitNode(src, key, value)
        
        # No statements parsed
        raise InvalidToken(src)

    def get_ident_list(self, src):
        """ Get list of identifiers """

        idents = []

        while src.t_type != T_EOL:
            if src.t_type != T_IDENT:
                raise InvalidToken(src)
            idents.append(src.t_val)
            src.next()
            if src.t_type == T_COMMA:
                src.next()
            elif src.t_type != T_EOL:
                break # raise InvalidToken(src)

        return idents

    def parse_use(self, src):
        """ Outer scope/shared variable using directive """
        
        src.next()
        vars = self.get_ident_list(src)
        
        return UseVariableNode(src, vars)

    def parse_import(self, src):
        """ Module refrences """

        src.next()
        is_native = src.t_type == T_NATIVE

        if is_native:
            src.next()

        module_names = self.get_ident_list(src)

        return ImportModuleNode(src, is_native, module_names)
        
    def parse_block(self, src, type):
        """ Block of statements """
        
        stop_tokens = { T_ELSEIF, T_ELSE, T_END }
        ast = BlockNode(src)
        
        if type == Parser.B_OUTER:
            self.root_node = ast
            src.next()
        
        while True:
            # Stop tokens
            if src.t_type == T_EOF:
                if type == Parser.B_OUTER:
                    return ast
                else:
                    raise InvalidToken(src)
            elif src.t_type in stop_tokens:
                if type == Parser.B_OUTER:
                    raise InvalidToken(src)
                elif type == Parser.B_FUNC and src.t_type != T_END:
                    raise InvalidToken(src)
                src.hold()
                return ast
            
            # Blank line
            if src.t_type == T_EOL:
                src.next()
                continue
            
            if src.t_type == T_FUNC:
                # Can define functions only in global scope
                if type != Parser.B_OUTER:
                    raise InvalidToken(src)
                src.next()
                func_def = self.parse_func(src)
                self.append_function(func_def)
            elif src.t_type == T_USE:
                if type == Parser.B_STMT:
                    raise InvalidToken(src)
                uses = self.parse_use(src)
                ast.statements.insert(0, uses)
            elif src.t_type == T_IMPORT:
                if type != Parser.B_OUTER:
                    raise InvalidToken(src)
                imports = self.parse_import(src)
                ast.statements.insert(0, imports)
            else:
                stmt = self.parse_stmt(src)
                ast.statements.append(stmt)
            
            self.require_cr(src)
        
        return ast