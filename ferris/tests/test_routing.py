import unittest
from ferris.core import routing


class TestClass(object):
    prefixes = ['pre']

    def method1(self):
        pass

    def method2(self, arg1, arg2):
        pass

    def pre_method1(self):
        pass

    def pre_method2(self, arg1, arg2):
        pass


class RoutingTest(unittest.TestCase):

    def testPartsFromMethod(self):

        self.assertEquals(
            routing.canonical_parts_from_method(TestClass.method1),
            {
                'prefix': None,
                'handler': 'test_class',
                'action': 'method1',
                'args': []
            }
        )

        self.assertEquals(
            routing.canonical_parts_from_method(TestClass.method2),
            {
                'prefix': None,
                'handler': 'test_class',
                'action': 'method2',
                'args': ['arg1', 'arg2']
            }
        )

        self.assertEquals(
            routing.canonical_parts_from_method(TestClass.pre_method1),
            {
                'prefix': 'pre',
                'handler': 'test_class',
                'action': 'method1',
                'args': []
            }
        )

        self.assertEquals(
            routing.canonical_parts_from_method(TestClass.pre_method2),
            {
                'prefix': 'pre',
                'handler': 'test_class',
                'action': 'method2',
                'args': ['arg1', 'arg2']
            }
        )

    def testPathFromParts(self):

        self.assertEquals(
            routing.path_from_canonical_parts(None, 'one', 'two', []),
            '/one/two'
        )

        self.assertEquals(
            routing.path_from_canonical_parts('pre', 'one', 'two', []),
            '/pre/one/two'
        )

        self.assertEquals(
            routing.path_from_canonical_parts(None, 'one', 'two', ['x', 'y']),
            '/one/two/<x>/<y>'
        )

        self.assertEquals(
            routing.path_from_canonical_parts('pre', 'one', 'two', ['x', 'y']),
            '/pre/one/two/<x>/<y>'
        )

    def testNameFromParts(self):

        self.assertEquals(
            routing.name_from_canonical_parts(None, 'one', 'two', []),
            'one-two'
        )

        self.assertEquals(
            routing.name_from_canonical_parts('pre', 'one', 'two', []),
            'pre-one-two'
        )

        self.assertEquals(
            routing.name_from_canonical_parts(None, 'one', 'two', ['x', 'y']),
            'one-two'
        )

        self.assertEquals(
            routing.name_from_canonical_parts('pre', 'one', 'two', ['x', 'y']),
            'pre-one-two'
        )
