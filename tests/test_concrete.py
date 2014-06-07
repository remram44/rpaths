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


class TestLists(unittest.TestCase):
    """Tests listing methods.
    """
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path.tempdir()
        cls.tmp.open('w', 'file').close()
        cls.tmp.open('w', u'r\xE9mi\'s file').close()
        d = cls.tmp.mkdir(u'r\xE9pertoire')
        d.open('w', 'file').close()
        d.mkdir('nested')
        d.open('w', 'last').close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.rmtree()

    def test_list_empty(self):
        d = self.tmp.mkdir('emptydir')
        try:
            self.assertEqual(d.listdir(), [])
        finally:
            d.rmdir()

    def test_listdir_posix(self):
        l1 = self.tmp.listdir()
        s1 = set(p.path for p in l1)
        self.assertEqual(len(l1), len(s1))
        if issubclass(Path, PosixPath):
            self.assertEqual(s1,
                             set([b'file', b'r\xC3\xA9mi\'s file',
                                  b'r\xC3\xA9pertoire']))
        else:
            self.assertEqual(s1,
                             set([u'file', u'r\xE9mi\'s file',
                                  u'r\xE9pertoire']))

        l2 = (self.tmp / u'r\xE9pertoire').listdir()
        s2 = set(p.path for p in l2)
        self.assertEqual(len(l2), len(s2))
        if issubclass(Path, PosixPath):
            self.assertEqual(s2,
                             set([b'file', b'nested', b'last']))
        else:
            self.assertEqual(s2,
                             set([u'file', u'nested', u'last']))
