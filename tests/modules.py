import unittest
from test_utils import compile_from_file, check_op_sequence

class Test_modules(unittest.TestCase):
    """ Module import tests """

    def test_import_native(self):
        lines = compile_from_file('import_native')
        find_ops = ['call.native', 'call.native', 'call.native']
        
        self.assertTrue(check_op_sequence(lines, find_ops))

    def test_import_script(self):
        lines = compile_from_file('import_script')
        find_ops = ['get', 'set', 'call.udf', 'call.udf', 'call.udf']
        
        self.assertTrue(check_op_sequence(lines, find_ops))

if __name__ == '__main__':
    unittest.main()
