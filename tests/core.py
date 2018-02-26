import unittest
from test_utils import compile_from_file, check_op_sequence

class Test_core(unittest.TestCase):
    """ Core tests """

    def test_elseif(self):
        lines = compile_from_file('elseif')
        find_ops = ['jmple', 'jmplt', 'jmple', 'jmple']
        
        self.assertTrue(check_op_sequence(lines, find_ops))

    def test_string_interpolation(self):
        lines = compile_from_file('str_inter')
        find_ops = [
            'concat', 'concat', 'concat', 'emit',
            'concat', 'concat', 'concat', 'emit',
            'concat', 'emit'
        ]

        self.assertTrue(check_op_sequence(lines, find_ops))

    def test_inc_dec(self):
        lines = compile_from_file('inc_dec')
        find_ops = ['load', 'load', 'add', 'load', 'load', 'add']

        self.assertTrue(check_op_sequence(lines, find_ops))

    def test_elems_assignment(self):
        lines = compile_from_file('struct_assignment')
        find_ops = ['set', 'get', 'get', 'get']

        self.assertTrue(check_op_sequence(lines, find_ops))

    def test_arrays(self):
        lines = compile_from_file('arrays')
        find_ops = ['emit']
        
        self.assertTrue(check_op_sequence(lines, find_ops))

    def test_foreach(self):
        lines = compile_from_file('for_each')
        find_ops = [
            'call.native', 'call.native', 'call.native', 'unload',
            'call.native', 'call.native', 'call.native', 'unload'
        ]

        self.assertTrue(check_op_sequence(lines, find_ops))

    def test_invoke(self):
        lines = compile_from_file('invoke')
        find_ops = [
            'load', 'invoke',
            'get', 'invoke',
            'load', 'invoke',
            'get', 'invoke'
        ]

        self.assertTrue(check_op_sequence(lines, find_ops))

if __name__ == '__main__':
    unittest.main()
