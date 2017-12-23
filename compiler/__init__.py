""" Front end """
import sys
from tokenizer import Tokenizer
from parser import Parser
from code_gen import CodeGen

def compile_buffer(input, output):
    """ Compile code from input buffer and output to another buffer """

    source = input.readlines()
    input.close()
        
    # Parse input
    tok = Tokenizer(source)
    parser = Parser(tok)
    ast = parser.parse_to_ast()
    
    # Generate code
    generator = CodeGen(ast, output)
    generator.load_module_defs('$builtin')
    generator.generate()


def compile_file(in_file_name, out_file_name):
    """ Compile code from file """
    
    in_file = open(in_file_name) if in_file_name is not None \
                                 else sys.stdin
    out_file = open(out_file_name, 'w') if out_file_name is not None \
                                        else sys.stdout
    compile_buffer(in_file, out_file)

if __name__ == '__main__':
    in_file_name = sys.argv[1] if len(sys.argv) > 1 else None
    out_file_name = sys.argv[2] if len(sys.argv) > 2 else None
    compile_file(in_file_name, out_file_name)
