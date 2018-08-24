""" AST nodes """

class ASTNode:
    """ Basic AST node """

    def __init__(self, tokenizer):
        self.line = tokenizer.line_number
    
    def accept(self, visitor):
        visitor.visit(self)

    def is_directive(self):
        """ Check if is a directive """

        return isinstance(self, UseVariableNode) or \
               isinstance(self, ImportModuleNode)
    
class NumberNode(ASTNode):
    """ Number literal """
    
    def __init__(self, tokenizer, value):
        ASTNode.__init__(self, tokenizer)
        self.value = float(value)
    
class StringNode(ASTNode):
    """ String literal """
    
    def __init__(self, tokenizer, text):
        ASTNode.__init__(self, tokenizer)
        self.value = text
    
class IdentifierNode(ASTNode):
    """ Identifier: variable/function/module etc. name """
    
    def __init__(self, tokenizer, name):
        ASTNode.__init__(self, tokenizer)
        self.name = name

class MathNode(ASTNode):
    """ Math action node """
    
    def __init__(self, tokenizer, left, right, op):
        ASTNode.__init__(self, tokenizer)
        self.l = left
        self.r = right
        self.op = op

class MinusNode(ASTNode):
    """ Math inversion """
    
    def __init__(self, tokenizer, value):
        ASTNode.__init__(self, tokenizer)
        self.expr = value

class CMPNode(ASTNode):
    """ Comparsion node """
    
    def __init__(self, tokenizer, one, two, op):
        ASTNode.__init__(self, tokenizer)
        self.l = one
        self.r = two
        self.op = op

class LogicNode(ASTNode):
    """ Logic expression    """
    
    def __init__(self, tokenizer, one, two, op):
        ASTNode.__init__(self, tokenizer)
        self.l = one
        self.r = two
        self.op = op
        
class StringOpNode(ASTNode):
    """ String concatenation """
    
    def __init__(self, tokenizer, one, two):
        ASTNode.__init__(self, tokenizer)
        self.op = '&'
        self.l = one
        self.r = two

class NegateNode(ASTNode):
    """ Logic negation """
    
    def __init__(self, tokenizer, expr):
        ASTNode.__init__(self, tokenizer)
        self.expr = expr

class CallNode(ASTNode):
    """ Function call """
    
    def __init__(self, tokenizer, name, args):
        ASTNode.__init__(self, tokenizer)
        self.name = name
        self.call_args = args

class InvokeNode(ASTNode):
    """ In-place function invocation """

    def __init__(self, tokenizer, expr, args):
        ASTNode.__init__(self, tokenizer)
        self.call_expr = expr
        self.call_args = args

class BlockNode(ASTNode):
    """ Statements sequence """
    
    def __init__(self, tokenizer):
        ASTNode.__init__(self, tokenizer)
        self.statements = []

class AssignNode(ASTNode):
    """ Variable assignment """
    
    def __init__(self, tokenizer, id, expr):
        ASTNode.__init__(self, tokenizer)
        self.name = id
        self.expr = expr

class CondNode(ASTNode):
    """ Conditional expression (if expression) """
    
    def __init__(self, tokenizer, cond, t_expr, f_expr):
        ASTNode.__init__(self, tokenizer)
        self.cond_expr = cond
        self.true_expr = t_expr
        self.false_expr = f_expr

class IfNode(ASTNode):
    """ If statement """
    
    def __init__(self, tokenizer, branches, else_branch):
        ASTNode.__init__(self, tokenizer)
        self.cond_branches = branches
        self.else_branch = else_branch

class ForWhileNode(ASTNode):
    """ While (for) loop """
    
    def __init__(self, tokenizer, cond, block):
        ASTNode.__init__(self, tokenizer)
        self.cond_expr = cond
        self.loop_block = block

class ForEachNode(ASTNode):
    """ Loop against iterable item """
    
    def __init__(self, tokenizer, expr, var_name, block):
        ASTNode.__init__(self, tokenizer)
        self.iter_expr = expr
        self.var_name = var_name
        self.loop_block = block

class LoopControlNode(ASTNode):
    """ Loop flow control: break/continue """

    def __init__(self, tokenizer, is_continue, depth = 1):
        ASTNode.__init__(self, tokenizer)
        self.continuing = is_continue
        self.depth = depth

class FuncNode(ASTNode):
    """ Function definition """
    
    def __init__(self, tokenizer, name, params, block, scope):
        ASTNode.__init__(self, tokenizer)
        self.name = name
        self.param_list = params
        self.func_block = block
        self.scope_name = scope
    
class ReturnNode(ASTNode):
    """ Return statement """
    
    def __init__(self, tokenizer, value):
        ASTNode.__init__(self, tokenizer)
        self.result = value

class EmitNode(ASTNode):
    """ Emit resultstatement """
    
    def __init__(self, tokenizer, name, value):
        ASTNode.__init__(self, tokenizer)
        self.name = name
        self.value = value
    
class ArrayNode(ASTNode):
    """ Array literal """
    
    def __init__(self, tokenizer, values = [], hashed = False):
        ASTNode.__init__(self, tokenizer)
        self.elements = values
        self.is_hash = hashed
        
class ItemGetNode(ASTNode):
    """ Get compound item node """
    
    def __init__(self, tokenizer, array, expr):
        ASTNode.__init__(self, tokenizer)
        self.array_expr = array
        self.index_expr = expr

class ItemSetNode(ASTNode):
    """ Set array element value node """

    def __init__(self, tokenizer, array, index, expr, op = None):
        ASTNode.__init__(self, tokenizer)
        self.array_expr = array
        self.index_expr = index
        self.elem_expr = expr
        self.op = op
        
class UseVariableNode(ASTNode):
    """ Using global variable node """
    
    def __init__(self, tokenizer, names):
        ASTNode.__init__(self, tokenizer)
        self.variables = names

class ImportModuleNode(ASTNode):
    """ Module reference node """

    def __init__(self, tokenizer, is_native, names):
        ASTNode.__init__(self, tokenizer)
        self.native = is_native
        self.modules = names

class FunctionRefNode(ASTNode):
    """ Function reference node """

    def __init__(self, tokenizer, name, mod_name = None):
        ASTNode.__init__(self, tokenizer)
        self.func_name = name
        self.module = mod_name

class NewObjNode(ASTNode):
    """ New object construction node """

    def __init__(self, tokenizer, hash):
        ASTNode.__init__(self, tokenizer)
        self.hash = hash