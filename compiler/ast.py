""" AST nodes """

class ASTNode:
    """ Basic AST node """
    
    def accept(self, visitor):
        visitor.visit(self)

    def is_directive(self):
        """ Check if is a directive """

        return isinstance(self, UseVariableNode) or \
               isinstance(self, ImportModuleNode)
    
class NumberNode(ASTNode):
    """ Number literal """
    
    def __init__(self, value):
        self.value = float(value)
    
class StringNode(ASTNode):
    """ String literal """
    
    def __init__(self, text):
        self.value = text
    
class IdentifierNode(ASTNode):
    """ Identifier: variable/function/module etc. name """
    
    def __init__(self, name):
        self.name = name

class MathNode(ASTNode):
    """ Math action node """
    
    def __init__(self, left, right, op):
        self.l = left
        self.r = right
        self.op = op

class MinusNode(ASTNode):
    """ Math inversion """
    
    def __init__(self, value):
        self.expr = value

class CMPNode(ASTNode):
    """ Comparsion node """
    
    def __init__(self, one, two, op):
        self.l = one
        self.r = two
        self.op = op

class LogicNode(ASTNode):
    """ Logic expression    """
    
    def __init__(self, one, two, op):
        self.l = one
        self.r = two
        self.op = op
        
class StringOpNode(ASTNode):
    """ String concatenation """
    
    def __init__(self, one, two):
        self.op = '&'
        self.l = one
        self.r = two

class NegateNode(ASTNode):
    """ Logic negation """
    
    def __init__(self, expr):
        self.expr = expr

class CallNode(ASTNode):
    """ Function call """
    
    def __init__(self, name, args):
        self.name = name
        self.call_args = args

class InvokeNode(ASTNode):
    """ In-place function invocation """

    def __init__(self, expr, args):
        self.call_expr = expr
        self.call_args = args

class BlockNode(ASTNode):
    """ Statements sequence """
    
    def __init__(self):
        self.statements = []

class AssignNode(ASTNode):
    """ Variable assignment """
    
    def __init__(self, id, expr):
        self.name = id
        self.expr = expr

class CondNode(ASTNode):
    """ Conditional expression (if expression) """
    
    def __init__(self, cond, t_expr, f_expr):
        self.cond_expr = cond
        self.true_expr = t_expr
        self.false_expr = f_expr

class IfNode(ASTNode):
    """ If statement """
    
    def __init__(self, branches, else_branch):
        self.cond_branches = branches
        self.else_branch = else_branch

class ForWhileNode(ASTNode):
    """ While (for) loop """
    
    def __init__(self, cond, block):
        self.cond_expr = cond
        self.loop_block = block

class ForEachNode(ASTNode):
    """ Loop against iterable item """
    
    def __init__(self, expr, var_name, block):
        self.iter_expr = expr
        self.var_name = var_name
        self.loop_block = block

class FuncNode(ASTNode):
    """ Function definition """
    
    def __init__(self, name, params, block):
        self.name = name
        self.param_list = params
        self.func_block = block
    
class ReturnNode(ASTNode):
    """ Return statement """
    
    def __init__(self, value):
        self.result = value

class EmitNode(ASTNode):
    """ Emit resultstatement """
    
    def __init__(self, name, value):
        self.name = name
        self.value = value
    
class ArrayNode(ASTNode):
    """ Array literal """
    
    def __init__(self, values = [], hashed = False):
        self.elements = values
        self.is_hash = hashed
        
class ItemGetNode(ASTNode):
    """ Get compound item node """
    
    def __init__(self, array, expr):
        self.array_expr = array
        self.index_expr = expr

class ItemSetNode(ASTNode):
    """ Set array element value node """

    def __init__(self, array, index, expr, op = None):
        self.array_expr = array
        self.index_expr = index
        self.elem_expr = expr
        self.op = op
        
class UseVariableNode(ASTNode):
    """ Using global variable node """
    
    def __init__(self, names):
        self.variables = names

class ImportModuleNode(ASTNode):
    """ Module reference node """

    def __init__(self, is_native, names):
        self.native = is_native
        self.modules = names
