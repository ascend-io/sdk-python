import unittest
import ascend.resource_definitions as resource


class TestResource(unittest.TestCase):

    def test_resolve_path(self):
        root = (None, None, None)
        ds = ('ds', None, None)
        df = ('ds', 'df', None)
        comp = ('ds', 'df', 'comp')
        base = 'base_path/'
        self.assertEqual(resource.resolve_path(base, root, ds), 'base_path/ds')
        self.assertEqual(resource.resolve_path(base, root, df), 'base_path/ds/df')
        self.assertEqual(resource.resolve_path(base, root, comp), 'base_path/ds/df/comp')
        self.assertEqual(resource.resolve_path(base, ds, ds), 'base_path/')
        self.assertEqual(resource.resolve_path(base, ds, df), 'base_path/df')
        self.assertEqual(resource.resolve_path(base, ds, comp), 'base_path/df/comp')
        self.assertEqual(resource.resolve_path(base, df, comp), 'base_path/comp')
