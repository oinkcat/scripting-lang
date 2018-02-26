""" Utils for unit testing """
import os
import io
import sys

sys.path.insert(0, '..')
import compiler

def compile_from_file(filename):
    """ Compile file and return output stream """

    in_file_name = os.path.join('./src', filename + '.l')
    out_file_name = os.path.join('./src', filename + '.lb')

    # Compile module
    in_file = open(in_file_name)
    resolver = compiler.LocalDependencyProvider(in_file_name)
    out_buffer = io.BytesIO()
    compiler.compile_buffer(in_file, out_buffer, resolver)

    # Save compiled code
    out_buffer.seek(0)
    code_lines = list(out_buffer.readlines())
    with open(out_file_name, 'w') as out_file:
        out_file.writelines(code_lines)

    return code_lines

def check_op_sequence(compiled_lines, opcodes):
    """ Check opcodes ocurrence in compiled code """

    opcodes.reverse()
    target = opcodes.pop()
    last_matched = False

    for line in compiled_lines:
        op_code = line.split(' ', 1)[0].strip()
        
        if op_code == target:
            if len(opcodes) == 0:
                last_matched = True
                break
            target = opcodes.pop()
            last_match = False
    
    return (len(opcodes) == 0) and last_matched