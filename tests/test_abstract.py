try:
    import unittest2 as unittest
except ImportError:
    import unittest

from rpaths import unicode, PY3, AbstractPath, PosixPath, WindowsPath


class TestAbstract(unittest.TestCase):
    def test_construct(self):
        """Tests building an AbstractPath."""
        with self.assertRaises(RuntimeError):
            AbstractPath('path/to/something')


class TestWindows(unittest.TestCase):
    """Tests for WindowsPath.
    """
    def test_construct(self):
        """Tests building paths."""
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
        """Tests getting string representations (repr/bytes/unicode)."""
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

    def test_parts(self):
        """Tests parent, ancestor, name, stem, ext."""
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
        self.assertEqual(absolute.unicodename, u'thing.h\xE9h\xE9')
        self.assertEqual(absolute.stem, u'thing')
        self.assertEqual(absolute.ext, u'.h\xE9h\xE9')

    def test_root(self):
        """Tests roots, drives and UNC shares."""
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
        self.assertFalse(b.is_absolute)
        self.assertEqual(split_root(c),
                         (u'\\', u'this\\is\\absolute'))
        self.assertTrue(c.is_absolute)
        self.assertEqual(split_root(d),
                         (u'C:\\', u'.'))
        self.assertTrue(d.is_absolute)
        self.assertEqual(d.root.path, u'C:\\')
        self.assertEqual(split_root(e),
                         (u'C:\\', u'also\\absolute'))
        # FIXME : normpath() doesn't behave consistently: puts \ at the end on
        # PY3, not on PY2.
        self.assertIn(split_root(f),
                      [(u'\\\\SOMEMACHINE\\share', u'some\\file'),
                       (u'\\\\SOMEMACHINE\\share\\', u'some\\file')])

    def test_rel_path_to(self):
        """Tests the rel_path_to method."""
        self.assertEqual(WindowsPath(u'\\var\\log\\apache2\\').rel_path_to(
                         u'\\var\\www\\cat.jpg').path,
                         u'..\\..\\www\\cat.jpg')
        self.assertEqual(WindowsPath(u'C:\\var\\log\\apache2\\').rel_path_to(
                         u'C:\\tmp\\access.log').path,
                         u'..\\..\\..\\tmp\\access.log')
        self.assertEqual(WindowsPath(u'var\\log').rel_path_to(
                         u'var\\log\\apache2\\access.log').path,
                         u'apache2\\access.log')
        self.assertEqual(WindowsPath(u'\\var\\log\\apache2').rel_path_to(
                         u'\\var\\log\\apache2').path,
                         u'.')
        self.assertEqual(WindowsPath(u'C:\\').rel_path_to(
                         u'C:\\var\\log\\apache2\\access.log').path,
                         u'var\\log\\apache2\\access.log')
        self.assertEqual(WindowsPath(u'\\tmp\\secretdir\\').rel_path_to(
                         u'\\').path,
                         u'..\\..')
        self.assertEqual(WindowsPath(u'C:\\tmp\\secretdir\\').rel_path_to(
                         u'D:\\other\\file.txt').path,
                         u'D:\\other\\file.txt')
        with self.assertRaises(TypeError):
            WindowsPath(u'C:\\mydir\\').rel_path_to(PosixPath('/tmp/file'))

    def test_lies_under(self):
        """ Tests the lies_under method."""
        self.assertTrue(WindowsPath(u'\\tmp')
                        .lies_under(u'\\'))
        self.assertFalse(WindowsPath(u'C:\\tmp')
                         .lies_under(u'C:\\var'))
        self.assertFalse(WindowsPath(u'\\tmp')
                         .lies_under(u'C:\\tmp'))
        self.assertFalse(WindowsPath(u'C:\\')
                         .lies_under(u'D:\\tmp'))
        self.assertTrue(WindowsPath(u'\\tmp\\some\\file\\here')
                        .lies_under(u'\\tmp\\some'))
        self.assertFalse(WindowsPath(u'\\tmp\\some\\file\\here')
                         .lies_under(u'\\tmp\\no'))
        self.assertFalse(WindowsPath(u'C:\\tmp\\some\\file\\here')
                         .lies_under(u'C:\\no\\tmp\\some'))
        self.assertFalse(WindowsPath(u'\\tmp\\some\\file\\here')
                         .lies_under(u'\\no\\some'))
        self.assertTrue(WindowsPath(u'C:\\tmp\\some\\file\\here')
                        .lies_under(u'C:\\tmp\\some\\file\\here'))
        self.assertTrue(WindowsPath(u'\\')
                        .lies_under(u'\\'))
        self.assertTrue(WindowsPath(u'')
                        .lies_under(u''))
        self.assertTrue(WindowsPath(u'test')
                        .lies_under(u''))
        self.assertFalse(WindowsPath(u'')
                         .lies_under(u'test'))
        self.assertFalse(WindowsPath(u'test')
                         .lies_under(u'\\'))


class TestPosix(unittest.TestCase):
    """Tests for PosixPath.
    """
    def test_construct(self):
        """Tests building paths."""
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
        if PY3:
            self.assertEqual(PosixPath(u'/tmp/r\uDCE9mi').path,
                             b'/tmp/r\xE9mi')

    def test_str(self):
        """Tests getting string representations (repr/bytes/unicode)."""
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

    def test_parts(self):
        """Tests parent, ancestor, name, stem, ext."""
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
        self.assertEqual(absolute.stem, b'thing')
        self.assertEqual(absolute.ext, b'.h\xC3\xA9h\xC3\xA9')

    def test_root(self):
        """Tests roots."""
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
        self.assertFalse(b.is_absolute)
        self.assertEqual(split_root(c),
                         (b'/', b'this/is/absolute'))
        self.assertTrue(c.is_absolute)
        self.assertEqual(split_root(d),
                         (b'/', b'.'))
        self.assertTrue(d.is_absolute)
        self.assertEqual(d.root.path, b'/')

    def test_rel_path_to(self):
        """Tests the rel_path_to method."""
        self.assertEqual(PosixPath(b'/var/log/apache2/').rel_path_to(
                         b'/var/www/cat.jpg').path,
                         b'../../www/cat.jpg')
        self.assertEqual(PosixPath(b'/var/log/apache2/').rel_path_to(
                         b'/tmp/access.log').path,
                         b'../../../tmp/access.log')
        self.assertEqual(PosixPath(b'var/log').rel_path_to(
                         b'var/log/apache2/access.log').path,
                         b'apache2/access.log')
        self.assertEqual(PosixPath(b'/var/log/apache2').rel_path_to(
                         b'/var/log/apache2').path,
                         b'.')
        self.assertEqual(PosixPath(b'/').rel_path_to(
                         b'/var/log/apache2/access.log').path,
                         b'var/log/apache2/access.log')
        self.assertEqual(PosixPath(b'/tmp/secretdir/').rel_path_to(
                         b'/').path,
                         b'../..')

    def test_lies_under(self):
        """ Tests the lies_under method."""
        self.assertTrue(PosixPath(b'/tmp')
                        .lies_under(b'/'))
        self.assertFalse(PosixPath(b'/tmp')
                         .lies_under(b'/var'))
        self.assertTrue(PosixPath(b'/tmp/some/file/here')
                        .lies_under(b'/tmp/some'))
        self.assertFalse(PosixPath(b'/tmp/some/file/here')
                         .lies_under(b'/tmp/no'))
        self.assertFalse(PosixPath(b'/tmp/some/file/here')
                         .lies_under(b'/no/tmp/some'))
        self.assertFalse(PosixPath(b'/tmp/some/file/here')
                         .lies_under(b'/no/some'))
        self.assertTrue(PosixPath(b'/tmp/some/file/here')
                        .lies_under(b'/tmp/some/file/here'))
        self.assertTrue(PosixPath(b'/')
                        .lies_under(b'/'))
        self.assertTrue(PosixPath(b'')
                        .lies_under(b''))
        self.assertTrue(PosixPath(b'test')
                        .lies_under(b''))
        self.assertFalse(PosixPath(b'')
                         .lies_under(b'test'))
        self.assertFalse(PosixPath(b'test')
                         .lies_under(b'/'))
