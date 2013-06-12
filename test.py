#!/usr/bin/env python
import unittest
from mock import Mock

if __name__ == '__main__':
    import os
    r = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    import sys
    sys.path.insert(0, r)

from .parser import parser
from .lexer import PLYCompatLexer
from .exceptions import CompileException
from .environment import Environment


class TestBase(unittest.TestCase):
    def run_code(self, i, namespace=None, debug=False):
        if namespace is None:
            namespace = {}
        root = self.compile(i, debug=debug)
        root.evaluate(namespace)
        return namespace

    def compile(self, code, debug=False):
        return parser.parse(code, lexer=PLYCompatLexer(debug=debug))


class TestAssignment(TestBase):
    def test_assignment(self):
        n = self.run_code('''a=1\nb=1''')
        self.assertEqual(n, {'a': 1, 'b': 1})

    def test_repeated_assignment(self):
        n = self.run_code('''a=1\na=2''')
        self.assertEqual(n, {'a': 2})

    def test_transitive_assignment(self):
        n = self.run_code('''a=3\nb=a''')
        self.assertEqual(n, {'a': 3, 'b': 3})

    def test_additive_assignment(self):
        n = self.run_code('''a=1\na+=2''')
        self.assertEqual(n, {'a': 3})

    def test_substractive_assignment(self):
        n = self.run_code('''a=1\na-=2''')
        self.assertEqual(n, {'a': -1})

    def test_multiplicative_assignment(self):
        n = self.run_code('''a=2\na*=2''')
        self.assertEqual(n, {'a': 4})

    def test_division_assignment(self):
        n = self.run_code('''a=8\na/=2''')
        self.assertEqual(n, {'a': 4})


class TestIf(TestBase):
    def test_if_false(self):
        n = self.run_code('''if 0\n  a=1''')
        self.assertEqual(n, {})

    def test_if_true(self):
        n = self.run_code('''if 1\n  a=1''')
        self.assertEqual(n, {'a': 1})

    def test_nested_if(self):
        n = self.run_code('''if 1\n  if 1\n    a=1''')
        self.assertEqual(n, {'a': 1})

    def test_nested_if_false(self):
        n = self.run_code('''if 0\n  if 1\n    a=1''')
        n = self.run_code('''if 1\n  if 0\n    a=1''', n)
        self.assertEqual(n, {})


class TestStatements(TestBase):
    def test_multiple_newlines(self):
        n = self.run_code('''a=1\n\nb=2''')
        self.assertEqual(n, {'a': 1, 'b': 2})

    def test_print_number(self):
        env = Environment()
        env.stdout = Mock()
        n = self.run_code('''print 1''', env)
        self.assertEqual(n, env)
        env.stdout.assert_called_with(1)

    def test_print_variable(self):
        env = Environment()
        env.stdout = Mock()
        n = self.run_code('''a=1\nprint a''', env)
        self.assertEqual(n, env)
        env.stdout.assert_called_with(1)

    def test_print_string(self):
        env = Environment()
        env.stdout = Mock()
        n = self.run_code('''print "test"''', env)
        self.assertEqual(n, env)
        env.stdout.assert_called_with("test")


class TestPartialParsing(unittest.TestCase):
    def test_partial_none(self):
        i = '''if 1'''
        root = parser.parse(i, lexer=PLYCompatLexer())
        self.assertIsNone(root)

    def test_partial_none2(self):
        i = '''if 1\n a=1'''
        root = parser.parse(i, lexer=PLYCompatLexer(auto_end=False))
        self.assertIsNone(root)

    def test_partial_ok(self):
        i = '''if 1\n a=1\nnop'''
        root = parser.parse(i, lexer=PLYCompatLexer(auto_end=False))
        n = {}
        root.evaluate(n)
        self.assertEqual(n, {'a': 1})

    def test_partial_fail3(self):
        i = '''if 1=\n a=1'''
        with self.assertRaises(CompileException):
            parser.parse(i, lexer=PLYCompatLexer(auto_end=False))


class TestMath(TestBase):
    def test_addition(self):
        n = self.run_code('''a=1+1''')
        self.assertEqual(n, {'a': 2})

    def test_subtraction(self):
        n = self.run_code('''a=2-1''')
        self.assertEqual(n, {'a': 1})

    def test_multiplication(self):
        n = self.run_code('''a=2*3''')
        self.assertEqual(n, {'a': 6})

    def test_division(self):
        n = self.run_code('''a=8/2''')
        self.assertEqual(n, {'a': 4})

    def test_multiplication_before_addition(self):
        n = self.run_code('''a=2+2*5''')
        self.assertEqual(n, {'a': 12})

    def test_paren(self):
        n = self.run_code('''a=(2+2)*5''')
        self.assertEqual(n, {'a': 20})

    def test_increment(self):
        n = self.run_code('''a=1\na=a+1''')
        self.assertEqual(n, {'a': 2})


class TestEnvironment(unittest.TestCase):
    def setUp(self):
        self.e = Environment()

    def test_simple(self):
        self.e['a'] = 1
        self.assertEqual(self.e['a'], 1)

    def test_overwrite(self):
        self.e['a'] = 1
        self.e['a'] = 2
        self.assertEqual(self.e['a'], 2)

    def test_undefined(self):
        with self.assertRaises(KeyError):
            self.e['b']

    def test_stack(self):
        self.e.push_stacklevel()
        self.e['a'] = 3
        self.assertEqual(self.e['a'], 3)
        self.e.pop_stacklevel()
        with self.assertRaises(KeyError):
            self.e['a']

    def test_stack_top_level(self):
        self.e['b'] = 1
        self.e.push_stacklevel()
        self.e.set_local_key('b', 2)
        self.assertEqual(self.e['b'], 2)
        self.e.pop_stacklevel()
        self.assertEqual(self.e['b'], 1)

    def test_stack_not_top_level(self):
        self.e['b'] = 1
        self.e.push_stacklevel()
        self.e['b'] = 2
        self.assertEqual(self.e['b'], 2)
        self.e.pop_stacklevel()
        self.assertEqual(self.e['b'], 2)

    def test_global_read(self):
        o = Mock()
        o.__getitem__ = Mock(return_value=3)
        o.__setitem__ = Mock()
        self.e.register_global('test', o)
        self.assertEqual(self.e['test'][1], 3)
        o.__getitem__.assert_called_once()
        self.e['test'][1] = 3
        o.__setitem__.assert_called_with(1, 3)
        self.assertEqual(self.e, Environment())


class TestEnvironmentWithParser(TestBase):
    def test_flat(self):
        n = self.run_code('''a=1''', Environment())
        self.assertEqual(n, Environment([{'a': 1}]))

    def test_assignment_variables(self):
        n = self.run_code('''a=1\nb=a''', Environment())
        self.assertEqual(n, Environment([{'a': 1, 'b': 1}]))

    def test_stacked(self):
        n = self.run_code('''c=0\nfor a in b\n c=c+1''', Environment([{'b': [1, 2, 3]}]))
        self.assertEqual(n, Environment([{'b': [1, 2, 3], 'c': 3}]))


class TestForloop(TestBase):
    def test_list_inline(self):
        n = self.run_code('''a=0\nfor i in [1,2,3]\n a=a+i''', Environment())
        self.assertEqual(n, Environment([{'a': 6}]))

    def test_list_from_variable(self):
        n = self.run_code('''a=0\nb=[2,3]\nfor i in b\n a=a+i''', Environment())
        self.assertEqual(n, Environment([{'a': 5, 'b': [2, 3]}]))


class TestListsAndDicts(TestBase):
    def test_list_part_read(self):
        n = self.run_code('''a=[1,2,3]\nb=a[0]''')
        self.assertEqual(n, {'a': [1, 2, 3], 'b': 1})

    def test_list_part_write(self):
        n = self.run_code('''a=[1,2,3]\na[0]=5''')
        self.assertEqual(n, {'a': [5, 2, 3]})

    def test_dict_part_read(self):
        n = self.run_code('''b=a["test"]''', Environment([{'a': {'test': 1}}]))
        self.assertEqual(n, Environment([{'a': {'test': 1}, 'b': 1}]))

    def test_dict_part_write(self):
        n = self.run_code('''a["foo"] = 3''', Environment([{'a': {}}]))
        self.assertEqual(n, Environment([{'a': {'foo': 3}}]))

    def test_dict_alt_read(self):
        n = self.run_code('''b=a.test''', Environment([{'a': {'test': 1}}]))
        self.assertEqual(n, Environment([{'a': {'test': 1}, 'b': 1}]))

    def test_dict_alt_write(self):
        n = self.run_code('''a.foo = 3''', Environment([{'a': {}}]))
        self.assertEqual(n, Environment([{'a': {'foo': 3}}]))


class TestFunctions(TestBase):
    def test_simple_call(self):
        e = Environment()
        e.register_global('testfun', lambda x, y: x + y)
        n = self.run_code('''b=testfun(1, 1)''', e)
        self.assertEqual(n, Environment([{'b': 2}]))


class TestErrorMessages(TestBase):
    def run_code_and_catch_errors(self, code):
        env = Environment()
        env.stdout = Mock()
        env.stderr = Mock()
        return self.run_code(code, env)

    def read_on_undefined_variable(self):
        n = self.run_code_and_catch_errors('''b=a''')
        n.stderr.assert_called_once()


if __name__ == '__main__':
    unittest.main()
