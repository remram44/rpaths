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
        """Tests cwd, in_dir."""
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

    def test_tempfile(self):
        """Tests tempfile."""
        fd, f = Path.tempfile()
        os.close(fd)
        try:
            self.assertTrue(f.exists())
            self.assertTrue(f.is_file())
            self.assertTrue(f.is_absolute)
        finally:
            f.remove()
            self.assertFalse(f.exists())


class TestLists(unittest.TestCase):
    """Tests listing methods.
    """
    @classmethod
    def setUpClass(cls):
        """Builds a test hierarchy."""
        cls.tmp = Path.tempdir()
        cls.tmp.open('w', 'file').close()
        cls.tmp.open('w', u'r\xE9mi\'s file').close()
        d = cls.tmp.mkdir(u'r\xE9pertoire')
        d.open('w', 'file').close()
        d.mkdir('nested')
        if issubclass(Path, PosixPath):
            (d / 'last').symlink('..')
        else:
            d.open('w', 'last').close()

    @classmethod
    def tearDownClass(cls):
        """Removes the test files."""
        cls.tmp.rmtree()

    def test_list_empty(self):
        """Lists an empty directory."""
        d = self.tmp.mkdir('emptydir')
        try:
            self.assertEqual(d.listdir(), [])
        finally:
            d.rmdir()

    def test_listdir(self):
        """Lists test directories."""
        l1 = list(self.tmp.listdir())
        s1 = set(p.path for p in l1)
        self.assertEqual(len(l1), len(s1))
        if issubclass(Path, PosixPath):
            expected = [b'file', b'r\xC3\xA9mi\'s file', b'r\xC3\xA9pertoire']
        else:
            expected = [u'file', u'r\xE9mi\'s file', u'r\xE9pertoire']
        expected = set(os.path.join(self.tmp.path, f) for f in expected)
        self.assertEqual(s1, expected)

        p2 = self.tmp / u'r\xE9pertoire'
        l2 = list(p2.listdir())
        s2 = set(p.path for p in l2)
        self.assertEqual(len(l2), len(s2))
        if issubclass(Path, PosixPath):
            expected = [b'file', b'nested', b'last']
        else:
            expected = [u'file', u'nested', u'last']
        expected = set(os.path.join(p2.path, f) for f in expected)
        self.assertEqual(s2, expected)

    def test_recursedir(self):
        """Uses recursedir to list a hierarchy."""
        l = list(self.tmp.recursedir())
        s = set(p.path for p in l)
        if issubclass(Path, PosixPath):
            expected = [b'file', b'r\xC3\xA9mi\'s file', b'r\xC3\xA9pertoire',
                        b'r\xC3\xA9pertoire/file', b'r\xC3\xA9pertoire/last',
                        b'r\xC3\xA9pertoire/nested']
        else:
            expected = [u'file', u'r\xE9mi\'s file', u'r\xE9pertoire',
                        u'r\xE9pertoire\\file', u'r\xE9pertoire\\last',
                        u'r\xE9pertoire\\nested']
        expected = set(os.path.join(self.tmp.path, f) for f in expected)
        self.assertEqual(s, expected)
