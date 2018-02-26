import unittest
from test_utils import compile_from_file, check_op_sequence

class Test_objects(unittest.TestCase):
    """ 'Objects' testing """

    def test_object(self):
        lines = compile_from_file('obj')
        find_ops = ['bind_refs', 'invoke']
        
        self.assertTrue(check_op_sequence(lines, find_ops))

    def test_builder_pattern(self):
        lines = compile_from_file('obj_builder')
        find_ops = ['bind_refs', 'invoke', 'invoke', 'invoke', 'emit']
        
        self.assertTrue(check_op_sequence(lines, find_ops))

if __name__ == '__main__':
    unittest.main()
