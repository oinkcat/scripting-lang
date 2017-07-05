""" Lexer and parser~ """

# TODO: Code generation with visitor pattern

import re
import random

# Token types
T_STRING = 0
T_COMMA = 1
T_NUMBER = 2
T_ASSIGN = 3
T_ADD = 4
T_MUL = 5
T_CMP = 6
T_NOT = 7
T_IF = 8
T_ELSE = 9
T_FOR = 10
T_FUNC = 11
T_RETURN = 12
T_END = 13
T_EMIT = 14
T_AS = 15
T_LOGIC = 16
T_IDENT = 17
T_LBR = 18
T_RBR = 19
T_LSBR = 20
T_RSBR = 21
T_SPACE = 22
T_COMMENT = 23
T_EOL = 100
T_EOF = -1

# Block types
B_OUTER = 0
B_FUNC = 1
B_STMT = 2

class Tokenizer:
  """ Performs string tokenization """

  TMPL_EXPR = '("[^"]+")|(,)|' + \
              '([0-9]+(?:\.[0-9]+)?)|' + \
              '(=)|' + \
              '([+\-])|([*/%])|' + \
              '(<=|>=|<|>|==|!=)|' + \
              '(not)|' + \
              '(if)|(else)|(for)|' + \
              '(func)|(return)|(end)|' + \
              '(emit)|(as)|' + \
              '(or|and|xor)|' + \
              '([_a-z][_0-9a-z]*)|' + \
              '(\()|(\))|(\[)|(\])|' + \
              '(\s+)|(#.+$)'

  def __init__(self, source):
    self.re = re.compile(Tokenizer.TMPL_EXPR, re.IGNORECASE)
    self.gen = self.tokenize(source)
    # Current token information
    self.t_type = None
    self.t_val = None
    self.retry = False

  def hold(self):
    """ Tell tokenizer to retry current token later """
    self.retry = True
    
  def next(self):
    """	Get next token """
    
    if not self.retry:
      try:
        token = self.gen.next()
        self.t_type, self.t_val = token
      except StopIteration:
        pass
    
    else:
      self.retry = False
      
  def tokenize(self, lines):
    """ Tokenize source lines """
    
    for line in lines:
      for token in self.tokenize_line(line):
        yield token
    
    yield (T_EOF, None)
    

  def tokenize_line(self, line):
    """ Get tokens from one source line """
  
    SKIP_TOKENS = [T_SPACE, T_COMMENT]
  
    prev_end = 0
    for t in self.re.finditer(line):
      tok_idx = 0
      if t.start() - prev_end > 0:
        seq = line[prev_end : t.start()]
        raise Exception("Unexpected sequence: %s" % seq)
      
      for val in t.groups():
        if val is not None:
          if tok_idx not in SKIP_TOKENS:
            yield (tok_idx, val)
            break
        tok_idx += 1
      prev_end = t.end()

    if prev_end != len(line):
      raise Exception("Unexpected sequence at end!")
    
    yield (T_EOL, None)

class InvalidToken(Exception):
  """ Invalid token occured """
  
  def __init__(self, src):
    msg = 'Invalid token: %s, %s' % (src.t_type, src.t_val)
    Exception.__init__(self, msg)
      
class ASTNode:
  """ Basic AST node """
  pass
  
class NumberNode(ASTNode):
  """ Number literal """
  
  def __init__(self, value):
    self.value = float(value)
  
class StringNode(ASTNode):
  """ String literal """
  
  def __init__(self, text):
    self.value = text
  
class VariableNode(ASTNode):
  """ Reference to variable """
  
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
  """ Logic expression  """
  
  def __init__(self, one, two, op):
    self.l = one
    self.r = two
    self.op = op

class NegateNode(ASTNode):
  """ Logic negation """
  
  def __init__(self, expr):
    self.expr = expr

class CallNode(ASTNode):
  """ Function call """
  
  def __init__(self, name, args):
    self.name = name
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
  
  def __init__(self, cond, t_part, f_part):
    self.cond_expr = cond
    self.true_branch = t_part
    self.false_branch = f_part

class ForWhileNode(ASTNode):
  """ While (for) loop """
  
  def __init__(self, cond, block):
    self.cond_expr = cond
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
  
  def __init__(self, values = []):
    self.elements = values
    
class ArrayIndexNode(ASTNode):
  """Array indexing node """
  
  def __init__(self, id, expr):
    self.name = id
    self.index_expr = expr
  
stack = []
    
def parse_factor(src):
  """ Atom or subexpression """

  src.next()
  
  # Value can be inverted
  inverted = src.t_type == T_ADD and src.t_val == '-'
  if inverted:
    src.next()    
  
  result = None
  if src.t_type == T_NUMBER:
    result = NumberNode(src.t_val)
  elif src.t_type == T_STRING:
    if inverted:
      raise InvaludToken(src)
    result = StringNode(src.t_val)
  elif src.t_type == T_IDENT:
    # Variable/array reference or function call
    ident = src.t_val
    src.next()
    if src.t_type == T_LBR:
      args = parse_arglist(src)
      result = CallNode(ident, args)
    elif src.t_type == T_LSBR:
      parse_expr(src)
      if src.t_type != T_RSBR:
        raise InvalidToken(src)
      result = ArrayIndexNode(ident, stack.pop())
    else:
      src.hold()
      result = VariableNode(ident)
  elif src.t_type == T_IF:
    src.next()
    result = parse_cond_expr(src)
  elif src.t_type == T_LBR:
    parse_expr(src)
    if src.t_type != T_RBR:
      raise InvalidToken(src)
    result = stack.pop()
  elif src.t_type == T_LSBR:
    if inverted:
      raise InvalidToken(src)
    result = parse_array(src)
  else:
    raise InvalidToken(src)
    
  if inverted:
    stack.append(MinusNode(result))
  else:
    stack.append(result)
  
def parse_morefactors(src):
  """ Operators priority: 1 """
  
  src.next()
  if src.t_type == T_MUL:
    op = src.t_val
    parse_factor(src)
    f2 = stack.pop()
    f1 = stack.pop()
    f_expr = MathNode(f1, f2, op)
    stack.append(f_expr)
    parse_morefactors(src)
  
def parse_moreterms(src):
  """ Operators priority: 2 """

  if src.t_type == T_ADD:
    op = src.t_val
    parse_term(src)
    t2 = stack.pop()
    t1 = stack.pop()
    t_expr = MathNode(t1, t2, op)
    stack.append(t_expr)
    parse_moreterms(src)

def parse_term(src):
  parse_factor(src)
  parse_morefactors(src)

def parse_morecmp(src):
  """ Operators priority: 3 """
  
  if src.t_type == T_CMP:
    op = src.t_val
    parse_cmp(src)
    c2 = stack.pop()
    c1 = stack.pop()
    c_expr = CMPNode(c1, c2, op)
    stack.append(c_expr)
    parse_morecmp(src)
  
def parse_cmp(src):
  parse_term(src)
  parse_moreterms(src)

def parse_moreconds(src):
  """ Operators priority: 4 """
  
  if src.t_type == T_LOGIC:
    op = src.t_val
    parse_cond(src)
    l2 = stack.pop()
    l1 = stack.pop()
    l_expr = LogicNode(l1, l2, op)
    stack.append(l_expr)
    parse_moreconds(src)

def parse_cond(src):
  negated = False
  src.next()
  if src.t_type == T_NOT:
    negated = True
  else:
    src.hold()

  parse_cmp(src)
  parse_morecmp(src)
  
  if negated:
    expr = stack.pop()
    stack.append(NegateNode(expr))
  
def parse_expr(src):
  """ Expression/subexpression """
  
  parse_cond(src)
  parse_moreconds(src)
  
def parse_arglist(src):
  """ Function call arguments list """
  
  delims = [T_COMMA, T_RBR]
  arg_exprs = []
  
  src.next()
  while src.t_type != T_RBR:
    # If first time
    if len(arg_exprs) == 0:
      src.hold()
    parse_expr(src)
    arg_exprs.append(stack.pop())
    if src.t_type not in delims:
      raise InvalidToken(src)
    
  return arg_exprs

def parse_cond_expr(src):
  """ If expression """
  
  if src.t_type != T_LBR:
    raise InvalidToken(src)
  # Condition
  parse_expr(src)
  cond = stack.pop()
  if src.t_type != T_COMMA:
    raise InvalidToken(src)
  # True branch expression
  parse_expr(src)
  true_expr = stack.pop()
  if src.t_type != T_COMMA:
    raise InvalidToken(src)
  # False branch expression
  parse_expr(src)
  false_expr = stack.pop()
  if src.t_type != T_RBR:
    raise InvalidToken(src)
  
  return CondNode(cond, true_expr, false_expr)
  
def require_cr(src):
  delimiters = [T_EOL, T_EOF]
  if src.t_type not in delimiters:
    raise InvalidToken(src)
  src.next()
  
def strip_cr(src):
  while src.t_type == T_EOL:
    src.next()

def parse_if_stmt(src):
  """ If statement """
  
  # Condition
  parse_expr(src)
  cond = stack.pop()
  require_cr(src)  
  
  # True block
  t_branch = parse_block(src, B_STMT)
  src.next()
 
  # False block (optional)
  f_branch = None
  if src.t_type == T_ELSE:
    src.next()
    require_cr(src)
    f_branch = parse_block(src, B_STMT)
    src.next()
  
  if src.t_type != T_END:
    raise InvalidToken(src)
  src.next()
    
  return IfNode(cond, t_branch, f_branch)

def parse_for(src):
  # For loop (loops?)
  
  # Condition
  parse_expr(src)
  cond = stack.pop()
  require_cr(src)
  
  # Looping statements block
  loop = parse_block(src, B_STMT)
  src.next()
  
  if src.t_type != T_END:
    raise InvalidToken(src)
  src.next()
  
  return ForWhileNode(cond, loop)

def parse_paramlist(src):
  """ Function parameters list """
  
  delims = [T_COMMA, T_RBR]
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

def parse_func(src):
  """ Function definition """
  
  # Name
  if src.t_type != T_IDENT:
    raise InvalidToken(src)
  id = src.t_val
  src.next()
  
  # Parameters list
  if src.t_type != T_LBR:
    raise InvalidToken(src)
  src.next()
  
  params = parse_paramlist(src)
  src.next()
  require_cr(src)
  
  # Function body
  body_block = parse_block(src, B_FUNC)
  src.next()
  if src.t_type != T_END:
    raise InvalidToken(src)
  src.next()
  require_cr(src)
  
  return FuncNode(id, params, body_block)

def parse_array(src):
  """ Array literal """
  
  elems = []
  
  
  while src.t_type != T_RSBR:
    src.next()
    strip_cr(src)
    if src.t_type != T_RSBR:
      src.hold()
      parse_expr(src)
      elems.append(stack.pop())
      strip_cr(src)
      if src.t_type != T_COMMA and src.t_type != T_RSBR:
        raise InvalidToken(src)
  
  return ArrayNode(elems)

def parse_stmt(src):
  """ Block level statement """
  
  if src.t_type == T_IDENT:
    # Assignment or function call
    name = src.t_val
    src.next()
    if src.t_type == T_ASSIGN:
      parse_expr(src)
      expr = stack.pop()
      return AssignNode(name, expr)
    elif src.t_type == T_LBR:
      args = parse_arglist(src)
      src.next()
      return CallNode(name, args)
  elif src.t_type == T_IF:
    # If statement
    return parse_if_stmt(src)
  elif src.t_type == T_FOR:
    # Loop
    return parse_for(src)
  elif src.t_type == T_RETURN:
    # Return from function
    src.next()
    value = None
    if src.t_type != T_EOL:
      src.hold()
      parse_expr(src)
      value = stack.pop()
    return ReturnNode(value)
  elif src.t_type == T_EMIT:
    # Yield result to host
    parse_expr(src)
    value = stack.pop()
    key = None
    if src.t_type == T_AS:
      src.next()
      if src.t_type != T_IDENT:
        raise InvalidToken(src)
      key = src.t_val
      src.next()
    return EmitNode(key, value)
  
  # No statements parsed
  raise InvalidToken(src)

def parse_block(src, type = B_OUTER):
  """ Block of statements """
  
  ast = BlockNode()
  
  if type == B_OUTER:
    src.next()
  
  while True:
      
    # Stop tokens
    if src.t_type == T_EOF:
      if type == B_OUTER:
        return ast
      else:
        raise InvalidToken(src)
    elif (src.t_type == T_ELSE) or \
         (src.t_type == T_END):
      if type == B_FUNC and src.t_type == T_ELSE:
        raise InvalidToken(src)
      src.hold()
      return ast
    
    # Blank line
    if src.t_type == T_EOL:
      src.next()
      continue
    
    if src.t_type == T_FUNC:
      # Can define functions only in global scope
      if type != B_OUTER:
        raise InvalidToken(src)
      src.next()
      func = parse_func(src)
      ast.statements.insert(0, func)
    else:
      stmt = parse_stmt(src)
      ast.statements.append(stmt)
    
    require_cr(src)
  
  return ast
  
def random_id():
  return random.randint(0, 10000)

def traverse_ast(node):
  """ Traverse and dump AST node info """
  
  if isinstance(node, MathNode) or \
     isinstance(node, CMPNode) or \
     isinstance(node, LogicNode):
    traverse_ast(node.l)
    traverse_ast(node.r)
    # Binary expression
    print(node.op)
  elif isinstance(node, NumberNode):
    # Integer/float number
    print(node.value)
  elif isinstance(node, StringNode):
    # Character string
    print(node.value)
  elif isinstance(node, VariableNode):
    # Variable identifier
    print('ID: %s' % node.name)
  elif isinstance(node, CallNode):
    # Function call
    for arg_expr in node.call_args:
      traverse_ast(arg_expr)
    print('CALL: %s' % node.name)
  elif isinstance(node, MinusNode):
    # Math inversion
    traverse_ast(node.expr)
    print('MINUS')
  elif isinstance(node, NegateNode):
    # NOT expression
    traverse_ast(node.expr)
    print('NOT')
  elif isinstance(node, BlockNode):
    # Sequence of statements
    for stmt in node.statements:
      traverse_ast(stmt)
  elif isinstance(node, AssignNode):
    # Assignment to variable
    traverse_ast(node.expr)
    print('STORE ID: %s' % node.name)
  elif isinstance(node, CondNode):
    # If expression
    traverse_ast(node.cond_expr)
    id = random_id()
    print('IF FALSE -> IFE_FB_%d' % id)
    traverse_ast(node.true_expr)
    print('-> IF_TR_%d' % id)
    print('IFE_FB_%d:' % id)
    traverse_ast(node.false_expr)
    print('IF_TR:')
  elif isinstance(node, IfNode):
    # If statement
    traverse_ast(node.cond_expr)
    id = random_id()
    print('IF FALSE -> IF_FB_%d' % id)
    traverse_ast(node.true_branch)
    if node.false_branch is not None:
      print('-> IF_TR_%d' % id)
      print('IF_FB_%d:' % id)
      traverse_ast(node.false_branch)
      print('IF_TR_%d:' % id)
    else:
      print('IF_FB_%d:' % id)
  elif isinstance(node, ForWhileNode):
    # While loop statement
    id = random_id()
    print('FOR_W_COND_%d:' % id)
    traverse_ast(node.cond_expr)
    print('IF FALSE -> FOR_W_END_%d' % id)
    traverse_ast(node.loop_block)
    print('-> FOR_W_COND_%d' % id)
    print('FOR_W_END_%d:' % id)
  elif isinstance(node, FuncNode):
    num_params = len(node.param_list)
    print('FUNC: %s.%d' % (node.name, num_params))
    traverse_ast(node.func_block)
    print('RET')
  elif isinstance(node, ReturnNode):
    # Return statement
    if node.result is not None:
      traverse_ast(node.result)
    print('RET')
  elif isinstance(node, EmitNode):
    # Emit result statement
    traverse_ast(node.value)
    if node.name is not None:
      print('EMIT "%s"' % node.name)
    else:
      print('EMIT')
  elif isinstance(node, ArrayNode):
    # Array literal
    for elem in node.elements:
      traverse_ast(elem)
    print('ARRAY: %d' % len(node.elements))
  elif isinstance(node, ArrayIndexNode):
    # Array indexing
    traverse_ast(node.index_expr)
    print('INDEX: %s' % node.name)
  else:
    raise Exception('Unknown node type (%s)!' % type(node))

def test_parse():
  print('Source lines: ')
  
  source = []
  while True:  
    try:
      line = raw_input()
      source.append(line)
    except EOFError:
      break
    
  tok = Tokenizer(source)  
  ast = parse_block(tok, B_OUTER)
  # Results
  print('')
  traverse_ast(ast)

if __name__ == '__main__':
  # Parse standard input
  test_parse()