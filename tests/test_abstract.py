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
        self.assertEqual((WindowsPath(u'Users\\R\xE9mi/Desktop') /
                          WindowsPath(b'pictures/m\xE9chant.jpg')).path,
                         u'Users\\R\xE9mi\\Desktop\\pictures\\m\xE9chant.jpg')

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

    def test_parent(self):
        relative = WindowsPath(u'directory/users\\r\xE9mi/file.txt')
        absolute = WindowsPath(u'\\some/other\\thing.h\xE9h\xE9')
        self.assertEqual(relative.parent.path,
                         u'directory\\users\\r\xE9mi')
        self.assertEqual(absolute.parent.path,
                         u'\\some\\other')
        self.assertEqual(absolute.ancestor(10).path,
                         u'\\')
        self.assertEqual(relative.name, u'file.txt')
        self.assertEqual(absolute.name, u'thing.h\xE9h\xE9')

    def test_root(self):
        a = WindowsPath(b'some/relative/path')
        b = WindowsPath(u'alsorelative')
        c = WindowsPath(b'/this/is/absolute')
        d = WindowsPath(u'C:\\')
        e = WindowsPath(b'C:\\also/absolute')
        f = WindowsPath(u'\\\\SOMEMACHINE\\share\\some\\file')

        def split_root(f):
            return tuple(p.path for p in f.split_root())

        self.assertEqual(split_root(a),
                         (u'.', u'some\\relative\\path'))
        self.assertEqual(split_root(b),
                         (u'.', u'alsorelative'))
        self.assertEqual(split_root(c),
                         (u'\\', u'this\\is\\absolute'))
        self.assertEqual(split_root(d),
                         (u'C:\\', u'.'))
        self.assertEqual(split_root(e),
                         (u'C:\\', u'also\\absolute'))
        # FIXME : normpath() doesn't behave consistently: puts \ at the end on
        # PY3, not on PY2.
        self.assertIn(split_root(f),
                      [(u'\\\\SOMEMACHINE\\share', u'some\\file'),
                       (u'\\\\SOMEMACHINE\\share\\', u'some\\file')])


class TestPosix(unittest.TestCase):
    """Tests for PosixPath.
    """
    def test_construct(self):
        self.assertEqual(PosixPath(u'/',
                                   PosixPath(b'r\xE9mis/dir'),
                                   u'with',
                                   'files.txt').path,
                         b'/r\xE9mis/dir/with/files.txt')
        with self.assertRaises(TypeError):
            PosixPath('/tmp/test', WindowsPath('folder'), 'cat.gif')
        self.assertEqual((PosixPath(b'/tmp/dir') /
                          PosixPath(u'r\xE9mis/files/')).path,
                         b'/tmp/dir/r\xC3\xA9mis/files')

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

    def test_parent(self):
        relative = PosixPath(b'directory/users/r\xE9mi/file.txt')
        absolute = PosixPath(u'/some/other/thing.h\xE9h\xE9')
        self.assertEqual(relative.parent.path,
                         b'directory/users/r\xE9mi')
        self.assertEqual(absolute.parent.path,
                         b'/some/other')
        self.assertEqual(absolute.ancestor(10).path,
                         b'/')
        self.assertEqual(relative.name, b'file.txt')
        self.assertEqual(absolute.name, b'thing.h\xC3\xA9h\xC3\xA9')
        self.assertEqual(absolute.unicodename, u'thing.h\xE9h\xE9')

    def test_root(self):
        a = PosixPath(b'some/relative/path')
        b = PosixPath(u'alsorelative')
        c = PosixPath(b'/this/is/absolute')
        d = PosixPath(u'/')

        def split_root(f):
            return tuple(p.path for p in f.split_root())

        # FIXME : This behaves weirdly because of normpath(). Do we want this?
        self.assertEqual(split_root(a),
                         (b'.', b'some/relative/path'))
        self.assertEqual(split_root(b),
                         (b'.', b'alsorelative'))
        self.assertEqual(split_root(c),
                         (b'/', b'this/is/absolute'))
        self.assertEqual(split_root(d),
                         (b'/', b'.'))
