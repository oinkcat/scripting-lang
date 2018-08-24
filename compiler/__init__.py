""" Front end """
import sys, traceback
import os
from tokenizer import Tokenizer, InvalidSequence
from l_parser import Parser, InvalidToken
from code_gen import CodeGen, CodeGenError
from linker import Linker, CompiledModuleLoader

OUT_DEBUG_MSG = True

def out_debug(msg, *args):
    """ Output debug message """

    if OUT_DEBUG_MSG:
        line = "%s\n" % msg
        sys.stderr.write(line % args)

class LocalDependencyProvider:
    """ Provide local importing modules """

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

        src_path = self._get_local(mod_name, self.__class__.EXT_SOURCE)
        bc_path = self._get_local(mod_name, self.__class__.EXT_COMPILED)

        if (src_path is None) and (bc_path is None):
            raise Exception('Required module %s not found!' % name)

        # Can we load compiled bytecode file
        if src_path is None:
            use_compiled = True
        elif bc_path is None:
            use_compiled = False
        else:
            src_mtime = os.stat(src_path).st_mtime
            bc_mtime = os.stat(bc_path).st_mtime
            use_compiled =  bc_mtime >= src_mtime

        if use_compiled:
            compiled_dep = CompiledModuleLoader().load(bc_path)
        else:
            with open(src_path) as dep_src_file:
                compiled_dep = compile_module_stream(mod_name, dep_src_file)
                # Save compiled module
                self._save_compiled_dependency(compiled_dep, src_path)

        detail = ' (compiled)' if use_compiled else ''
        out_debug('Linking with: %s%s', mod_name, detail)

        return compiled_dep

    def _get_local(self, name, ext):
        """ Get requested module file name """

        mod_filename = name + ext
        mod_file_path = os.path.join(self.base_dir, mod_filename)

        if os.path.isfile(mod_file_path):
            # Check local file
            return mod_file_path
        else:
            # Check library file
            lib_file_path = os.path.join(self.lib_path, mod_filename)
            return lib_file_path if os.path.isfile(lib_file_path) else None

    def _save_compiled_dependency(self, module, src_path):
        """ Save compiled dependent module """

        compiled_filename = module.name + self.__class__.EXT_COMPILED
        dirname = os.path.dirname(src_path)
        compiled_path = os.path.join(dirname, compiled_filename)
        
        with open(compiled_path, 'w') as out_file:
            module.save(out_file)

def compile_module_stream(name, stream):
    """ Compile one module from source stream """

    out_debug('Compiling: %s', name)

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

    try:
        compile_buffer(in_file, out_file, files_resolver)
    except (InvalidSequence, InvalidToken, CodeGenError) as e:
        sys.stderr.write("\033[91mScript compile exception!\n")
        sys.stderr.write("%s\033[0m\n" % e.message)
        traceback.print_exc(file=sys.stdout)
    except Exception:
        raise

if __name__ == '__main__':
    in_file_name = sys.argv[1] if len(sys.argv) > 1 else None
    out_file_name = sys.argv[2] if len(sys.argv) > 2 else None
    compile_file(in_file_name, out_file_name)
