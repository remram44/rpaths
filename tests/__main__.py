import locale
import os
import sys
try:
    import unittest2 as unittest2
    sys.modules['unittest'] = unittest2
except ImportError:
    pass
import unittest


top_level = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
start_dir = os.path.join(top_level, 'tests')
if top_level not in sys.path:
    sys.path.insert(0, top_level)


sys.path.append(start_dir)


locale.setlocale(locale.LC_ALL, 'C')


class Program(unittest.TestProgram):
    def createTests(self):
        if self.testNames is None:
            self.test = self.testLoader.discover(
                    start_dir=start_dir,
                    pattern='test_*.py',
                    top_level_dir=top_level)
        else:
            self.test = self.testLoader.loadTestsFromNames(self.testNames)

Program()
