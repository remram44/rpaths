from __future__ import unicode_literals

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
        self.assertEqual(WindowsPath('C:\\',
                                     WindowsPath('some/dir'),
                                     'with',
                                     'files.txt').path,
                         'C:\\some\\dir\\with\\files.txt')
        with self.assertRaises(TypeError):
            WindowsPath(WindowsPath('C:\\somedir'), PosixPath('file.sh'))
        self.assertEqual((WindowsPath('Users\\R\xE9mi/Desktop') /
                          WindowsPath(b'pictures/m\xE9chant.jpg')).path,
                         'Users\\R\xE9mi\\Desktop\\pictures\\m\xE9chant.jpg')
        self.assertEqual((WindowsPath('C:\\dir') /
                          WindowsPath('D:\\other')).path,
                         'D:\\other')

    def test_plus(self):
        """Tests the plus operator."""
        self.assertEqual((WindowsPath('some\\file.txt') + '.bak').path,
                         'some\\file.txt.bak')
        with self.assertRaises(TypeError):
            WindowsPath('some\\file.txt') + WindowsPath('.bak')
        with self.assertRaises(ValueError):
            WindowsPath('some\\file.txt') + '.bak/kidding'
        with self.assertRaises(ValueError):
            WindowsPath('some\\file.txt') + '/backup'

    def test_str(self):
        """Tests getting string representations (repr/bytes/unicode)."""
        latin = WindowsPath('C:\\r\xE9mi')
        nonlatin = WindowsPath('C:\\you like\u203D.txt')
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
                         'C:\\r\xe9mi')
        self.assertEqual(unicode(nonlatin),
                         'C:\\you like\u203d.txt')

    def test_parts(self):
        """Tests parent, ancestor, name, stem, ext."""
        relative = WindowsPath('directory/users\\r\xE9mi/file.txt')
        absolute = WindowsPath('\\some/other\\thing.h\xE9h\xE9')
        self.assertEqual(relative.parent.path,
                         'directory\\users\\r\xE9mi')
        self.assertEqual(absolute.parent.path,
                         '\\some\\other')
        self.assertEqual(absolute.ancestor(10).path,
                         '\\')
        self.assertEqual(relative.name, 'file.txt')
        self.assertEqual(absolute.name, 'thing.h\xE9h\xE9')
        self.assertEqual(absolute.unicodename, 'thing.h\xE9h\xE9')
        self.assertEqual(absolute.stem, 'thing')
        self.assertEqual(absolute.ext, '.h\xE9h\xE9')

    def test_root(self):
        """Tests roots, drives and UNC shares."""
        a = WindowsPath(b'some/relative/path')
        b = WindowsPath('alsorelative')
        c = WindowsPath(b'/this/is/absolute')
        d = WindowsPath('C:\\')
        e = WindowsPath(b'C:\\also/absolute')
        f = WindowsPath('\\\\SOMEMACHINE\\share\\some\\file')

        def split_root(f):
            return tuple(p.path for p in f.split_root())

        self.assertEqual(split_root(a),
                         ('.', 'some\\relative\\path'))
        self.assertEqual(split_root(b),
                         ('.', 'alsorelative'))
        self.assertFalse(b.is_absolute)
        self.assertEqual(split_root(c),
                         ('\\', 'this\\is\\absolute'))
        self.assertTrue(c.is_absolute)
        self.assertEqual(split_root(d),
                         ('C:\\', '.'))
        self.assertTrue(d.is_absolute)
        self.assertEqual(d.root.path, 'C:\\')
        self.assertEqual(split_root(e),
                         ('C:\\', 'also\\absolute'))
        # FIXME : normpath() doesn't behave consistently: puts \ at the end on
        # PY3, not on PY2.
        self.assertIn(split_root(f),
                      [('\\\\SOMEMACHINE\\share', 'some\\file'),
                       ('\\\\SOMEMACHINE\\share\\', 'some\\file')])

    def test_rel_path_to(self):
        """Tests the rel_path_to method."""
        self.assertEqual(WindowsPath('\\var\\log\\apache2\\').rel_path_to(
                         '\\var\\www\\cat.jpg').path,
                         '..\\..\\www\\cat.jpg')
        self.assertEqual(WindowsPath('C:\\var\\log\\apache2\\').rel_path_to(
                         'C:\\tmp\\access.log').path,
                         '..\\..\\..\\tmp\\access.log')
        self.assertEqual(WindowsPath('var\\log').rel_path_to(
                         'var\\log\\apache2\\access.log').path,
                         'apache2\\access.log')
        self.assertEqual(WindowsPath('\\var\\log\\apache2').rel_path_to(
                         '\\var\\log\\apache2').path,
                         '.')
        self.assertEqual(WindowsPath('C:\\').rel_path_to(
                         'C:\\var\\log\\apache2\\access.log').path,
                         'var\\log\\apache2\\access.log')
        self.assertEqual(WindowsPath('\\tmp\\secretdir\\').rel_path_to(
                         '\\').path,
                         '..\\..')
        self.assertEqual(WindowsPath('C:\\tmp\\secretdir\\').rel_path_to(
                         'D:\\other\\file.txt').path,
                         'D:\\other\\file.txt')
        with self.assertRaises(TypeError):
            WindowsPath('C:\\mydir\\').rel_path_to(PosixPath('/tmp/file'))

    def test_lies_under(self):
        """Tests the lies_under method."""
        self.assertTrue(WindowsPath('\\tmp')
                        .lies_under('\\'))
        self.assertFalse(WindowsPath('C:\\tmp')
                         .lies_under('C:\\var'))
        self.assertFalse(WindowsPath('\\tmp')
                         .lies_under('C:\\tmp'))
        self.assertFalse(WindowsPath('C:\\')
                         .lies_under('D:\\tmp'))
        self.assertTrue(WindowsPath('\\tmp\\some\\file\\here')
                        .lies_under('\\tmp\\some'))
        self.assertFalse(WindowsPath('\\tmp\\some\\file\\here')
                         .lies_under('\\tmp\\no'))
        self.assertFalse(WindowsPath('C:\\tmp\\some\\file\\here')
                         .lies_under('C:\\no\\tmp\\some'))
        self.assertFalse(WindowsPath('\\tmp\\some\\file\\here')
                         .lies_under('\\no\\some'))
        self.assertTrue(WindowsPath('C:\\tmp\\some\\file\\here')
                        .lies_under('C:\\tmp\\some\\file\\here'))
        self.assertTrue(WindowsPath('\\')
                        .lies_under('\\'))
        self.assertTrue(WindowsPath('')
                        .lies_under(''))
        self.assertTrue(WindowsPath('test')
                        .lies_under(''))
        self.assertFalse(WindowsPath('')
                         .lies_under('test'))
        self.assertFalse(WindowsPath('test')
                         .lies_under('\\'))

    def test_comparisons(self):
        """Tests the comparison operators."""
        self.assertTrue(WindowsPath('\\tmp') == WindowsPath('\\tmp'))
        self.assertFalse(WindowsPath('C:\\file') != 'c:\\FILE')
        self.assertTrue('c:\\FILE' == WindowsPath('C:\\file'))
        self.assertFalse(WindowsPath('C:\\file') == WindowsPath('C:\\dir'))
        self.assertFalse(WindowsPath('some/file') == PosixPath('some/file'))

        self.assertTrue(WindowsPath('path/to/file1') < 'path/to/file2')
        self.assertFalse('path/to/file1' >= WindowsPath('path/to/file2'))

        if PY3:
            with self.assertRaises(TypeError):
                WindowsPath('some/file') < PosixPath('other/file')


class TestPosix(unittest.TestCase):
    """Tests for PosixPath.
    """
    def test_construct(self):
        """Tests building paths."""
        self.assertEqual(PosixPath('/',
                                   PosixPath(b'r\xE9mis/dir'),
                                   'with',
                                   'files.txt').path,
                         b'/r\xE9mis/dir/with/files.txt')
        with self.assertRaises(TypeError):
            PosixPath('/tmp/test', WindowsPath('folder'), 'cat.gif')
        self.assertEqual((PosixPath(b'/tmp/dir') /
                          PosixPath('r\xE9mis/files/')).path,
                         b'/tmp/dir/r\xC3\xA9mis/files')
        if PY3:
            self.assertEqual(PosixPath('/tmp/r\uDCE9mi').path,
                             b'/tmp/r\xE9mi')
        self.assertEqual((PosixPath(b'/home/test') /
                          PosixPath('/var/log')).path,
                         b'/var/log')

    def test_plus(self):
        """Tests the plus operator."""
        self.assertEqual((PosixPath('some/file.txt') + '.bak').path,
                         b'some/file.txt.bak')
        with self.assertRaises(TypeError):
            PosixPath('some/file.txt') + PosixPath('.bak')
        with self.assertRaises(ValueError):
            PosixPath('some/file.txt') + '.bak/kidding'
        with self.assertRaises(ValueError):
            PosixPath('some/file.txt') + '/backup'

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
                         '/tmp/r\xE9mi')
        self.assertEqual(unicode(nonutf),
                         '/tmp/r\uFFFDmi')

    def test_parts(self):
        """Tests parent, ancestor, name, stem, ext."""
        relative = PosixPath(b'directory/users/r\xE9mi/file.txt')
        absolute = PosixPath('/some/other/thing.h\xE9h\xE9')
        self.assertEqual(relative.parent.path,
                         b'directory/users/r\xE9mi')
        self.assertEqual(absolute.parent.path,
                         b'/some/other')
        self.assertEqual(absolute.ancestor(10).path,
                         b'/')
        self.assertEqual(relative.name, b'file.txt')
        self.assertEqual(absolute.name, b'thing.h\xC3\xA9h\xC3\xA9')
        self.assertEqual(absolute.unicodename, 'thing.h\xE9h\xE9')
        self.assertEqual(absolute.stem, b'thing')
        self.assertEqual(absolute.ext, b'.h\xC3\xA9h\xC3\xA9')

    def test_root(self):
        """Tests roots."""
        a = PosixPath(b'some/relative/path')
        b = PosixPath('alsorelative')
        c = PosixPath(b'/this/is/absolute')
        d = PosixPath('/')

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

    def test_comparisons(self):
        """Tests the comparison operators."""
        self.assertTrue(PosixPath(b'/tmp/r\xE9mi') == b'/tmp/r\xE9mi')
        self.assertTrue(PosixPath(b'/file') != b'/FILE')
        self.assertFalse(PosixPath(b'file') == PosixPath(b'dir'))
        self.assertFalse(WindowsPath('some/file') == PosixPath('some/file'))

        self.assertTrue(PosixPath(b'path/to/file1') < b'path/to/file2')
        self.assertFalse(b'path/to/file1' >= PosixPath(b'path/to/file2'))

        if PY3:
            with self.assertRaises(TypeError):
                WindowsPath('some/file') < PosixPath('other/file')
