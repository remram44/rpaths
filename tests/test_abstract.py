try:
    import unittest2 as unittest
except ImportError:
    import unittest

from rpaths import unicode, PosixPath, WindowsPath


class TestWindows(unittest.TestCase):
    """Tests for WindowsPath.
    """
    def test_construct(self):
        self.assertEqual(WindowsPath(u'C:\\',
                                     WindowsPath('some/dir'),
                                     u'with',
                                     'files.txt').path,
                         u'C:\\some\\dir\\with\\files.txt')
        with self.assertRaises(TypeError):
            WindowsPath(WindowsPath('C:\\somedir'), PosixPath('file.sh'))
        self.assertEqual((WindowsPath(u'Users\\Desktop') /
                          WindowsPath('pictures/cat.jpg')).path,
                         u'Users\\Desktop\\pictures\\cat.jpg')

    def test_str(self):
        latin = WindowsPath(u'C:\\r\xE9mi')
        nonlatin = WindowsPath(u'C:\\you like\u203D.txt')
        # repr()
        self.assertEqual(repr(latin),
                         "WindowsPath(u'C:\\\\r\\xe9mi')")
        self.assertEqual(repr(nonlatin),
                         "WindowsPath(u'C:\\\\you like\\u203d.txt')")
        # bytes()
        self.assertEqual(bytes(latin),
                         b'C:\\r\xe9mi')
        self.assertEqual(bytes(nonlatin),
                         b'C:\\you like?.txt')
        # unicode()
        self.assertEqual(unicode(latin),
                         u'C:\\r\xe9mi')
        self.assertEqual(unicode(nonlatin),
                         u'C:\\you like\u203d.txt')


class TestPosix(unittest.TestCase):
    """Tests for PosixPath.
    """
    def test_construct(self):
        self.assertEqual(PosixPath(u'/',
                                   PosixPath('some/dir'),
                                   u'with',
                                   'files.txt').path,
                         b'/some/dir/with/files.txt')
        with self.assertRaises(TypeError):
            PosixPath('/tmp/test', WindowsPath('folder'), 'cat.gif')
        self.assertEqual((PosixPath('/tmp/dir') /
                          PosixPath('some/files/')).path,
                         b'/tmp/dir/some/files')

    def test_str(self):
        utf = PosixPath(b'/tmp/r\xC3\xA9mi')
        nonutf = PosixPath(b'/tmp/r\xE9mi')
        # repr()
        self.assertEqual(repr(utf),
                         "PosixPath(b'/tmp/r\\xc3\\xa9mi')")
        self.assertEqual(repr(nonutf),
                         "PosixPath(b'/tmp/r\\xe9mi')")
        # bytes()
        self.assertEqual(bytes(utf),
                         b'/tmp/r\xC3\xA9mi')
        self.assertEqual(bytes(nonutf),
                         b'/tmp/r\xE9mi')
        # unicode()
        self.assertEqual(unicode(utf),
                         u'/tmp/r\xE9mi')
        self.assertEqual(unicode(nonutf),
                         u'/tmp/r\uFFFDmi')
