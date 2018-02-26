""" Front end """
import sys
import os
from tokenizer import Tokenizer
from parser import Parser
from code_gen import CodeGen
from linker import Linker

class LocalDependencyProvider:
    """ Provide compiled modules """

    EXT_SOURCE = '.l'
    EXT_COMPILED = '.lb'

    def __init__(self, src_filename):
        if src_filename is not None:
            self.base_dir = os.path.dirname(src_filename)
        else:
            self.base_dir = os.path.expanduser('~')

        # Library modules path
        compiler_path = os.path.dirname(__file__)
        self.lib_path = os.path.realpath(compiler_path + '/../lib')

    def get_dependency(self, mod_name):
        """ Get dependent module """

        dep_file = self._get_local_file(mod_name, self.__class__.EXT_SOURCE)
        return compile_module_stream(mod_name, dep_file)

    def _get_local_file(self, name, ext):
        mod_filename = name + ext
        mod_file_path = os.path.join(self.base_dir, mod_filename)

        if os.path.isfile(mod_file_path):
            # Check local file
            return open(mod_file_path)
        else:
            # Check library file
            lib_file_path = os.path.join(self.lib_path, mod_filename)
            if os.path.isfile(lib_file_path):
                return open(lib_file_path)
            else:
                raise Exception('Required module %s not found!' % name)


def compile_module_stream(name, stream):
    """ Compile one module from source stream """

    with stream:
        # Parse module source
        tok = Tokenizer(stream.xreadlines())
        parser = Parser(tok)
        ast = parser.parse_to_ast()
    
        # Generate intermediate code
        generator = CodeGen(ast, name)
        generator.load_module_defs('$builtin')
        compiled = generator.generate()

        return compiled


def compile_buffer(input, output, resolver):
    """ Compile code from input buffer and output to another buffer """

    compiled_main = compile_module_stream('main', input)
    # Link modules
    linker = Linker(compiled_main, resolver)
    compiled_whole = linker.link()
    compiled_whole.save(output)


def compile_file(in_file_name, out_file_name):
    """ Compile code from file """
    
    in_file = open(in_file_name) if in_file_name is not None \
                                 else sys.stdin
    out_file = open(out_file_name, 'w') if out_file_name is not None \
                                        else sys.stdout

    files_resolver = LocalDependencyProvider(in_file_name)
    compile_buffer(in_file, out_file, files_resolver)

if __name__ == '__main__':
    test_filename = '/home/igor/shared/compiler_service/tests/obj.l'
    in_file_name = sys.argv[1] if len(sys.argv) > 1 else test_filename
    out_file_name = sys.argv[2] if len(sys.argv) > 2 else None
    compile_file(in_file_name, out_file_name)
