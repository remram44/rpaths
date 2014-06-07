import os
import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from rpaths import unicode, Path, PosixPath, WindowsPath


windows_only = unittest.skipUnless(issubclass(Path, WindowsPath),
                                   "Only runs on Windows")
posix_only = unittest.skipUnless(issubclass(Path, PosixPath),
                                 "Only runs on POSIX")


class TestConcrete(unittest.TestCase):
    """Tests for Path.

    Because this tests the concrete Path, it needs to be run on both Windows
    and POSIX to ensure everything is correct.
    """
    def test_cwd(self):
        cwd = os.getcwd()

        if os.name == 'nt' and isinstance(cwd, bytes):
            cwd = cwd.decode('mbcs')
        elif os.name != 'nt' and isinstance(cwd, unicode):
            cwd = cwd.encode(sys.getfilesystemencoding())
        self.assertEqual(Path.cwd().path, cwd)
        tmp = Path.tempdir()
        with tmp.in_dir():
            self.assertEqual(Path.cwd(), tmp)
        self.assertNotEqual(Path.cwd(), tmp)
        self.assertTrue(tmp.exists())
        tmp.rmdir()
        self.assertFalse(tmp.exists())
