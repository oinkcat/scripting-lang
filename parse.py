""" Lexer, parser and code generator """

import re
import sys

# Token types
T_STRING = 0
T_COMMA = 1
T_HASHKEY = 2
T_NUMBER = 3
T_ADD = 4
T_MUL = 5
T_CMP = 6
T_ASSIGN = 7
T_CONCAT = 8
T_LBR = 9
T_RBR = 10
T_LSBR = 11
T_RSBR = 12
T_LCBR = 13
T_RCBR = 14
T_SPACE = 15
T_COMMENT = 16
T_IDENT = 17
# Literal tokens
T_NOT = 18
T_IF = 19
T_ELSE = 20
T_FOR = 21
T_FUNC = 22
T_RETURN = 23
T_END = 24
T_USE = 25
T_EMIT = 26
T_AS = 27
T_LOGIC = 28
T_EOL = 100
T_EOF = -1

class InvalidSequence(Exception):
	""" Invalid sequence on input """
	
	def __init__(self, line_num, line, seq):
		args = (seq, line_num, line)
		msg = "Invalid sequence on input: %s\nLine: %d, %s" % args
		Exception.__init__(self, msg)
<<<<<<< HEAD

class InvalidToken(Exception):
	""" Invalid token occured """
	
	def __init__(self, src):
		args = (src.t_type, src.t_val, src.line_number, src.line)
		msg = 'Invalid token: %s, %s\nLine: %d, %s' % args
		Exception.__init__(self, msg)

class Tokenizer:
	""" Performs string tokenization """

=======

class InvalidToken(Exception):
	""" Invalid token occured """
	
	def __init__(self, src):
		args = (src.t_type, src.t_val, src.line_number, src.line)
		msg = 'Invalid token: %s, %s\nLine: %d, %s' % args
		Exception.__init__(self, msg)

class Tokenizer:
	""" Performs string tokenization """

>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
	# Complex templates
	TMPL_MAIN = '("[^"]+")|(,)|' + \
				'([0-9a-z_]+:)|' + \
				'([0-9]+(?:\.[0-9]+)?)|' + \
				'([+\-])|([*/%])|' + \
				'(<=|>=|<|>|==|!=)|' + \
				'(=)|(&)|' + \
				'(\()|(\))|(\[)|(\])|(\{)|(\})|' + \
				'(\s+)|(#.+$)|' + \
				'([$_a-z][_0-9a-z]*)'
				
	# Simple literal templates
	TMPL_WORD = '(not)|' + \
				'(if)|(else)|(for)|' + \
				'(func)|(return)|(end)|(use)|' + \
				'(emit)|(as)|' + \
				'(or|and|xor)'

	def __init__(self, source):
		self.re_main = re.compile(Tokenizer.TMPL_MAIN, re.IGNORECASE)
		self.re_word = re.compile(Tokenizer.TMPL_WORD, re.IGNORECASE)
		self.gen = self.tokenize(source)
		# Current token information
		self.t_type = None
		self.t_val = None
		self.line_number = 0
		self.line = None
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
		
		for num, line in enumerate(lines):
			self.line_number = num + 1
			self.line = line
			for token in self.tokenize_line(line):
				yield token
		
		yield (T_EOF, None)
		

	def tokenize_line(self, line):
		""" Get tokens from one source line """
	
		SKIP_TOKENS = {T_SPACE, T_COMMENT}
	
		prev_end = 0
		for t in self.re_main.finditer(line):
			# Check match position
			if t.start() - prev_end > 0:
				seq = line[prev_end : t.start()]
				raise InvalidSequence(self.line_number, line, seq)
			
			tok_idx = None
			tok_val = None
			matched_groups = t.groups()
			
			# Check matching token
			for idx, val in enumerate(matched_groups):
				if not (val is None or idx in SKIP_TOKENS):
					tok_idx, tok_val = idx, val
					break
			
			if tok_idx is not None:
				# Check if keyword matched
				if tok_idx == T_IDENT:
					word_matches = self.re_word.findall(tok_val)
					if len(word_matches) > 0:
						matches = word_matches[0]
						for i in xrange(0, len(matches)):
							if tok_val == matches[i]:
								tok_idx += i + 1
								break
						
				yield (tok_idx, tok_val)
			
			prev_end = t.end()

		if prev_end != len(line):
			raise Exception("Unexpected sequence at end!")
		
		yield (T_EOL, None)
			
class ASTNode:
	""" Basic AST node """
	
	def accept(self, visitor):
		visitor.visit(self)
	
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
	""" Logic expression	"""
	
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
	
	def __init__(self, values = [], hashed = False):
		self.elements = values
		self.is_hash = hashed
		
class ArrayIndexNode(ASTNode):
	"""Array indexing node """
	
	def __init__(self, id, expr):
<<<<<<< HEAD
		self.array_expr = id
=======
		# TODO: name (string) -> array_expr (ASTNode)
		self.name = id
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
		self.index_expr = expr
		
class UseVariableNode(ASTNode):
	""" Using global variable node """
	
	def __init__(self, names):
		self.variables = names


class Parser:
	""" Language statements parser """

	# Block types
	B_OUTER = 0
	B_FUNC = 1
	B_STMT = 2

	def __init__(self, tokenizer):
		self.stack = []
		self.tokens_source = tokenizer
		
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
			result = NumberNode(src.t_val)
		elif src.t_type == T_STRING:
			if inverted:
				raise InvalidToken(src)
			result = StringNode(src.t_val)
		elif src.t_type == T_IDENT:
			# Variable/array reference or function call
			ident = src.t_val
			src.next()
			if src.t_type == T_LBR:
				args = self.parse_arglist(src)
				result = CallNode(ident, args)
			elif src.t_type == T_LSBR:
				self.parse_expr(src)
				if src.t_type != T_RSBR:
					raise InvalidToken(src)
<<<<<<< HEAD
				array_var = VariableNode(ident)
				result = ArrayIndexNode(array_var, self.stack.pop())
=======
				result = ArrayIndexNode(ident, self.stack.pop())
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
			else:
				src.hold()
				result = VariableNode(ident)
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
			self.stack.append(MinusNode(result))
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
			f_expr = MathNode(f1, f2, op)
			self.stack.append(f_expr)
			self.parse_morefactors(src)
		
	def parse_moreterms(self, src):
		""" Operators priority: 2 """

		if src.t_type == T_ADD:
			op = src.t_val
			self.parse_term(src)
			t2 = self.stack.pop()
			t1 = self.stack.pop()
			t_expr = MathNode(t1, t2, op)
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
			c_expr = CMPNode(c1, c2, op)
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
			l_expr = LogicNode(l1, l2, op)
			self.stack.append(l_expr)
			self.parse_moreconds(src)

	def parse_cond(self, src):
		""" Logic operators """
		
		negated = False
		src.next()
		if src.t_type == T_NOT:
			negated = True
		else:
			src.hold()

		self.parse_cmp(src)
		self.parse_morecmp(src)
		
		if negated:
			expr = self.stack.pop()
			self.stack.append(NegateNode(expr))
		
	def parse_moreconcats(self, src):
		""" Operators priority: 5 """
		
		if src.t_type == T_CONCAT:
			self.parse_concat(src)
			sc2 = self.stack.pop()
			sc1 = self.stack.pop()
			sc_expr = StringOpNode(sc1, sc2)
			self.stack.append(sc_expr)
			self.parse_moreconcats(src)

	def parse_concat(self, src):
		""" String concatenation """
		
		self.parse_cond(src)
		self.parse_moreconds(src)
			
	def parse_expr(self, src):
		""" Expression/subexpression """
		
		self.parse_concat(src)
		self.parse_moreconcats(src)
		
	def parse_arglist(self, src):
		""" Function call arguments list """
		
		delims = [T_COMMA, T_RBR]
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
		
		return CondNode(cond, true_expr, false_expr)
		
	def require_cr(self, src):
		delimiters = [T_EOL, T_EOF]
		if src.t_type not in delimiters:
			raise InvalidToken(src)
		src.next()
		
	def strip_cr(self, src):
		while src.t_type == T_EOL:
			src.next()

	def parse_if_stmt(self, src):
		""" If statement """
		
		# Condition
		self.parse_expr(src)
		cond = self.stack.pop()
		self.require_cr(src)	   
		
		# True block
		t_branch = self.parse_block(src, Parser.B_STMT)
		src.next()
	 
		# False block (optional)
		f_branch = None
		if src.t_type == T_ELSE:
			src.next()
			self.require_cr(src)
			f_branch = self.parse_block(src, Parser.B_STMT)
			src.next()
		
		if src.t_type != T_END:
			raise InvalidToken(src)
		src.next()
			
		return IfNode(cond, t_branch, f_branch)

	def parse_for(self, src):
		""" For loop (loops?) """
		
		# Condition
		self.parse_expr(src)
		cond = self.stack.pop()
		self.require_cr(src)
		
		# Looping statements block
		loop = self.parse_block(src, Parser.B_STMT)
		src.next()
		
		if src.t_type != T_END:
			raise InvalidToken(src)
		src.next()
		
		return ForWhileNode(cond, loop)

	def parse_paramlist(self, src):
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

	def parse_func(self, src):
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
		
		params = self.parse_paramlist(src)
		src.next()
		self.require_cr(src)
		
		# Function body
		body_block = self.parse_block(src, Parser.B_FUNC)
		src.next()
		if src.t_type != T_END:
			raise InvalidToken(src)
		src.next()
		self.require_cr(src)
		
		return FuncNode(id, params, body_block)

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
		
		return ArrayNode(elems, False)
		
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
		
		return ArrayNode(elems, True)

	def parse_stmt(self, src):
		""" Block level statement """
		
		if src.t_type == T_IDENT:
			# Assignment or function call
			name = src.t_val
			src.next()
			if src.t_type == T_ASSIGN:
				self.parse_expr(src)
				expr = self.stack.pop()
				return AssignNode(name, expr)
			elif src.t_type == T_LBR:
				args = self.parse_arglist(src)
				src.next()
				return CallNode(name, args)
		elif src.t_type == T_IF:
			# If statement
			return self.parse_if_stmt(src)
		elif src.t_type == T_FOR:
			# Loop
			return self.parse_for(src)
		elif src.t_type == T_RETURN:
			# Return from function
			src.next()
			value = None
			if src.t_type != T_EOL:
				src.hold()
				self.parse_expr(src)
				value = self.stack.pop()
			return ReturnNode(value)
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
			return EmitNode(key, value)
		
		# No statements parsed
		raise InvalidToken(src)

	def parse_use(self, src):
		""" Global variable using directive """
		
		vars = []
		src.next()
		
		while src.t_type != T_EOL:
			if src.t_type != T_IDENT:
				raise InvalidToken(src)
			vars.append(src.t_val)
			src.next()
			if src.t_type == T_COMMA:
				src.next()
			elif src.t_type != T_EOL:
				raise InvalidToken(src)
		
		return UseVariableNode(vars)
		
	def parse_block(self, src, type):
		""" Block of statements """
		
		ast = BlockNode()
		
		if type == Parser.B_OUTER:
			src.next()
		
		while True:
				
			# Stop tokens
			if src.t_type == T_EOF:
				if type == Parser.B_OUTER:
					return ast
				else:
					raise InvalidToken(src)
			elif (src.t_type == T_ELSE) or \
				 (src.t_type == T_END):
				if type == Parser.B_FUNC and src.t_type == T_ELSE:
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
				func = self.parse_func(src)
				ast.statements.insert(0, func)
			elif src.t_type == T_USE:
				if type != Parser.B_FUNC:
					raise InvalidToken(src)
				uses = self.parse_use(src)
				ast.statements.insert(0, uses)
			else:
				stmt = self.parse_stmt(src)
				ast.statements.append(stmt)
			
			self.require_cr(src)
		
		return ast
		
<<<<<<< HEAD
class Scope:
	""" Global or function scope """
	
	def __init__(self, name):
		self.name = name
		self.variables = dict()
		self.global_refs = set()
		
class CodeGen:
	""" Code generator with some optimizations """
	
	
	DEFS_FILEEXT = '.ld'
	
	# External definitions type
	EXT_CONST = 'const'
	EXT_FUNC = 'func'
=======
class CodeGen:
	""" Code generator """
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
	
	# Section identifiers
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
	
<<<<<<< HEAD
	JMP_OPCODES = {
=======
	JMP_TYPES = {
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
		'<': 'jmplt', '<=': 'jmple',
		'>': 'jmpgt', '>=': 'jmpge',
		'==': 'jmpeq', '!=': 'jmpne'
	}
	
<<<<<<< HEAD
	CMP_INVERSE = {
		'<': '>=', '>': '<=',
		'<=': '>', '>=': '<',
		'==': '!=', '!=': '=='
	}
	
	def __init__(self, root_node, out_file):
		self.ast = root_node
		self.output_file = out_file
		self.ext_defines = {
			'false': CodeGen.EXT_CONST,
			'true': CodeGen.EXT_CONST
		}
		self.scopes = []
		# Indexes of opcodes with global variables
		self.global_var_gen_idxs = []
		self.generated = []
		self.const_data = []
=======
	def __init__(self, root_node):
		self.ast = root_node
		self.scopes = []
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
		self.entry_node = None
		self.last_op = None
		self.last_jmp_id = 0
		
<<<<<<< HEAD
	def load_module_defs(self, mod_name):
		""" Load module function definitions """
		
		mod_filename = mod_name + CodeGen.DEFS_FILEEXT
		defs_file = open(mod_filename)
		
		for def_item in defs_file.xreadlines():
			name = def_item.strip()
			if len(name) > 0 and name[0] != '#':
				if '.' in name:
					func_name = name[0:name.find('.')]
					self.ext_defines[func_name] = CodeGen.EXT_FUNC
				else:
					self.ext_defines[name] = CodeGen.EXT_CONST
				
		defs_file.close()
		
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
					  % (var_name, self.get_scope())
				raise Exception(error_msg)
			
	def is_const_array(self, node):
		""" Check if array contains only const values """
		
		for elem in node.elements:
			if not isinstance(elem, NumberNode) and \
			   not isinstance(elem, StringNode):
				return False
				
		return True
		
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
=======
	def get_scope():
		""" Get current scope name """
		
		return self.scopes[len(self.scopes) - 1]

	def new_jmp_id(self):
		self.last_jmp_id += 1
		return self.last_jmp_id

	def emit(self, op, args_str = None):
		""" Emit opcode """
		
		self.last_op = op
		output = op
		if args_str != None:
			output += ' ' + args_str
		
		print(output)
		
	def emit_if_cond(self, node, true_branch_label):
		""" Emit condition expression """
		
		if isinstance(node.cond_expr, CMPNode):
			node.cond_expr.l.accept(self)
			node.cond_expr.r.accept(self)
			jmp_op = CodeGen.JMP_TYPES[node.cond_expr.op]
			self.emit(jmp_op, true_branch_label)
		else:
			node.cond_expr.accept(self)
			self.emit('cmp 1')
			self.emit('jmpeq', true_branch_label)
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
		
	def generate(self):
		""" Start code generation """
		
		if self.ast is None:
			raise Exception('No AST specified!')
		
		# Find function definitions section
		root_statements = self.ast.statements
		if isinstance(root_statements[0], FuncNode):
			self.emit(CodeGen.SECTION_FUNCS)
			
		# Find entry point
		for stmt in root_statements:
			if not isinstance(stmt, FuncNode):
				self.entry_node = stmt
				break
		
<<<<<<< HEAD
		# Traverse AST
		self.scopes.append(Scope('global'))
		self.ast.accept(self)
		
		# Resolve global variable indexes
		if len(self.global_var_gen_idxs) > 0:
			self.resolve_global_vars()
		
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
		
	def emit_if_common(self, node, has_else, branch_label):
		""" Emit common part of if expression and if statement """
		
		if isinstance(node.cond_expr, CMPNode):
			node.cond_expr.l.accept(self)
			node.cond_expr.r.accept(self)
			cmp_op = node.cond_expr.op if has_else \
				     else CodeGen.CMP_INVERSE[node.cond_expr.op]
			jmp_op = CodeGen.JMP_OPCODES[cmp_op]
			self.emit(jmp_op, branch_label)
		else:
			node.cond_expr.accept(self)
			cmp_arg = 'true' if has_else else 'false'
			self.emit('load.const', cmp_arg)
			self.emit('jmpeq', branch_label)
		
=======
		self.scopes.append('global')
		self.ast.accept(self)

>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
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
			node.l.accept(self)
			node.r.accept(self)
			if isinstance(node, LogicNode):
				self.emit(node.op)
			else:
				self.emit(CodeGen.COMMON_OPS[node.op])
		elif isinstance(node, NumberNode):
			# Integer/float number
			self.emit('load', str(node.value))
		elif isinstance(node, StringNode):
			# Character string
			self.emit('load', node.value)
		elif isinstance(node, VariableNode):
			# Variable identifier
<<<<<<< HEAD
			if self.ext_defines.has_key(node.name):
				self.emit('load.const', node.name)
			else:
				var_idx = self.get_scope_var(node.name)
				if var_idx is not None:
					self.emit('load', '#' + str(var_idx))
				else:
					self.add_global_var_ref('load', node.name)
=======
			self.emit('load', node.name)
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
		elif isinstance(node, CallNode):
			# Function call
			for arg_expr in node.call_args:
				arg_expr.accept(self)
<<<<<<< HEAD
			if self.ext_defines.has_key(node.name):
				# External function
				self.emit('call', node.name)
			else:
				# Defined function
				self.emit('invoke', node.name)
=======
				self.emit('call', node.name)
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
		elif isinstance(node, MinusNode):
			# Math inversion
			node.expr.accept(self)
			self.emit('load -1')
			self.emit('mul')
		elif isinstance(node, NegateNode):
			# NOT expression
			node.expr.accept(self)
			self.emit('not')
		elif isinstance(node, BlockNode):
			# Sequence of statements
			for stmt in node.statements:
				stmt.accept(self)
		elif isinstance(node, AssignNode):
			# Assignment to variable
			node.expr.accept(self)
<<<<<<< HEAD
			var_idx = self.put_scope_var(node.name)
			if var_idx is not None:
				self.emit('store', str(var_idx))
			else:
				self.add_global_var_ref('store', node.name)
=======
			self.emit('store', node.name)
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
		elif isinstance(node, CondNode):
			# If expression
			id = self.new_jmp_id()
			true_label = 'IFE_TB_%d' % id
<<<<<<< HEAD
			self.emit_if_common(node, True, true_label)
=======
			self.emit_if_cond(node, true_label)
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
			node.false_expr.accept(self)
			self.emit('jmp', 'IFE_%d' % id)
			self.emit(true_label + ':')
			node.true_expr.accept(self)
			self.emit('IFE_%d:' % id)
		elif isinstance(node, IfNode):
			# If statement
			id = self.new_jmp_id()
<<<<<<< HEAD
			end_label = 'IF_%d' % id
			if node.false_branch is not None:
				true_label = 'IF_TB_%d' % id
				self.emit_if_common(node, True, true_label)
				node.false_branch.accept(self)
				self.emit('jmp', 'IF_%d' % id)
				self.emit(true_label + ':')
			else:
				self.emit_if_common(node, False, end_label)
			node.true_branch.accept(self)
			self.emit(end_label + ':')
=======
			true_label = 'IF_TB_%d' % id
			self.emit_if_cond(node, true_label)
			if node.false_branch is not None:
				node.false_branch.accept(self)
				self.emit('jmp', 'IF_%d' % id)
			self.emit(true_label + ':')
			node.true_branch.accept(self)
			self.emit('IF_%d:' % id)
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
		elif isinstance(node, ForWhileNode):
			# While loop statement
			id = self.new_jmp_id()
			true_label = 'FOR_LOOP_%d' % id
			self.emit('FOR_COND_%d:' % id)
<<<<<<< HEAD
			self.emit_if_common(node, True, true_label)
=======
			self.emit_if_cond(node, true_label)
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
			self.emit('jmp', 'FOR_END_%d' % id)
			self.emit(true_label + ':')
			node.loop_block.accept(self)
			self.emit('jmp', 'FOR_COND_%d' % id)
			self.emit('FOR_END_%d:' % id)
		elif isinstance(node, FuncNode):
			# Function definition
<<<<<<< HEAD
			self.scopes.append(Scope(node.name))
			for param_name in node.param_list:
				self.put_scope_var(param_name)
=======
			self.scopes.append(node.name)
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
			num_params = len(node.param_list)
			self.emit('%s.%d:' % (node.name, num_params))
			node.func_block.accept(self)
			if not self.last_op == 'ret':
				self.emit('ret')
			self.scopes.pop()
		elif isinstance(node, ReturnNode):
			# Return statement
			if node.result is not None:
				node.result.accept(self)
			self.emit('ret')
		elif isinstance(node, EmitNode):
			# Emit result statement
			node.value.accept(self)
			if node.name is not None:
				self.emit('emit', '"%s"' % node.name)
			else:
				self.emit('emit')
		elif isinstance(node, ArrayNode):
			# Array/hash literal
			num_elems = len(node.elements)
			if node.is_hash:
				for key, elem in node.elements:
					self.emit('load', '"%s"' % key)
					elem.accept(self)
				self.emit('mk_hash', str(num_elems))
			else:
<<<<<<< HEAD
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
		elif isinstance(node, ArrayIndexNode):
			# Array indexing
			node.array_expr.accept(self)
			node.index_expr.accept(self)
			self.emit('get')
		elif isinstance(node, UseVariableNode):
			# Directive for using global variable(s)
			scope = self.get_scope()
			scope.global_refs.update(node.variables)
		else:
			raise Exception('Unknown node type (%s)!' % type(node))
			
	def write_out(self):
		""" Output generated code to file """
		
		def out_line(line):
			self.output_file.write(line + "\n")
			
		def out_const_array(array):
			elem_values = [str(elem.value) for elem in array.elements]
			out_line(' '.join(elem_values))
		
		if len(self.const_data) > 0:
			out_line(CodeGen.SECTION_DATA)
			for data_item in self.const_data:
				if isinstance(data_item, ArrayNode):
					out_const_array(data_item)
				else:
					raise Exception('Only constant array supported as data!')
			
		for code_item in self.generated:
			out_line(code_item)
=======
				for elem in node.elements:
					elem.accept(self)
				self.emit('mk_array', str(num_elems))
		elif isinstance(node, ArrayIndexNode):
			# Array indexing
			node.index_expr.accept(self)
			self.emit('get', str(node.name))
		elif isinstance(node, UseVariableNode):
			# Directive for using global variable(s)
			self.emit('; Using globals:', ', '.join(node.variables))
		else:
			raise Exception('Unknown node type (%s)!' % type(node))
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8

def parse_file(file_name):
	""" Parse code from stdin """
	
	# Read input file lines
	in_file = open(file_name) if file_name is not None \
							  else sys.stdin
	source = in_file.readlines()
	in_file.close()
		
	# Parse input
	tok = Tokenizer(source)
	parser = Parser(tok)
	ast = parser.parse_to_ast()
	
	# Generate code
<<<<<<< HEAD
	generator = CodeGen(ast, sys.stdout)
	generator.load_module_defs('builtin')
=======
	generator = CodeGen(ast)
>>>>>>> c541abd72b4a54a3a80d2e91c1bbcbb80f762bb8
	generator.generate()

if __name__ == '__main__':
	in_file_name = sys.argv[1] if len(sys.argv) > 1 else None
	parse_file(in_file_name)
