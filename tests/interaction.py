import unittest
from test_utils import compile_from_file, check_op_sequence

class Test_interaction(unittest.TestCase):
    """ Script interaction tests """

    def test_shared_vars(self):
        lines = compile_from_file('use_shared')
        find_ops = ['.shared', 'Name', 'load', 'emit', 'load', 'emit']
        
        self.assertTrue(check_op_sequence(lines, find_ops))

    def test_events(self):
        lines = compile_from_file('event')
        find_ops = [
            'mk_ref.udf', 'call.native',
            'mk_ref.udf', 'call.native', 'call.native'
        ]
        
        self.assertTrue(check_op_sequence(lines, find_ops))

if __name__ == '__main__':
    unittest.main()
