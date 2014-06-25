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
        cls.tmp.open('w', u'r\xE9mi\'s thing').close()
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

    def compare_paths(self, actual, expected, root):
        actual = set(p.path for p in actual)
        self.assertEqual(len(actual), len(expected))
        expected = set(os.path.join(root.path, f) for f in expected)
        self.assertEqual(actual, expected)

    def test_listdir(self):
        """Lists test directories."""
        l1 = list(self.tmp.listdir())
        if issubclass(Path, PosixPath):
            expected = [b'file', b'r\xC3\xA9mi\'s thing', b'r\xC3\xA9pertoire']
        else:
            expected = [u'file', u'r\xE9mi\'s thing', u'r\xE9pertoire']
        self.compare_paths(l1, expected, self.tmp)

        l1f = list(self.tmp.listdir('*e'))
        if issubclass(Path, PosixPath):
            expected = [b'file', b'r\xC3\xA9pertoire']
        else:
            expected = [u'file', u'r\xE9pertoire']
        self.compare_paths(l1f, expected, self.tmp)

        l1d = list(self.tmp.listdir(lambda p: p.is_dir()))
        if issubclass(Path, PosixPath):
            expected = [b'r\xC3\xA9pertoire']
        else:
            expected = [u'r\xE9pertoire']
        self.compare_paths(l1d, expected, self.tmp)

        p2 = self.tmp / u'r\xE9pertoire'
        l2 = list(p2.listdir())
        if issubclass(Path, PosixPath):
            expected = [b'file', b'nested', b'last']
        else:
            expected = [u'file', u'nested', u'last']
        self.compare_paths(l2, expected, p2)

        l2f = list(p2.listdir('*e'))
        if issubclass(Path, PosixPath):
            expected = [b'file']
        else:
            expected = [u'file']
        self.compare_paths(l2f, expected, p2)

    def test_recursedir(self):
        """Uses recursedir to list a hierarchy."""
        l = list(self.tmp.recursedir())
        if issubclass(Path, PosixPath):
            expected = [b'file', b'r\xC3\xA9mi\'s thing', b'r\xC3\xA9pertoire',
                        b'r\xC3\xA9pertoire/file', b'r\xC3\xA9pertoire/last',
                        b'r\xC3\xA9pertoire/nested']
        else:
            expected = [u'file', u'r\xE9mi\'s thing', u'r\xE9pertoire',
                        u'r\xE9pertoire\\file', u'r\xE9pertoire\\last',
                        u'r\xE9pertoire\\nested']
        self.compare_paths(l, expected, self.tmp)
        self.compare_paths(list(self.tmp.recursedir('*')), expected, self.tmp)

        lf = list(self.tmp.recursedir('*e'))
        if issubclass(Path, PosixPath):
            expected = [b'file', b'r\xC3\xA9pertoire',
                        b'r\xC3\xA9pertoire/file']
        else:
            expected = [u'file', u'r\xE9pertoire',
                        u'r\xE9pertoire\\file']
        self.compare_paths(lf, expected, self.tmp)
