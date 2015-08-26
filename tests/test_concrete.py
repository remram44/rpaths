from __future__ import unicode_literals

import os
import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from rpaths import unicode, dict_union, Path, PosixPath, WindowsPath, \
    Pattern, pattern2re


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
        tmp = Path.tempdir().resolve()
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

    def test_rel_path_to(self):
        self.assertEqual(Path('some/prefix/and/a/directory/').rel_path_to(
                         'some/prefix/path/to/cat.jpg'),
                         Path('../../../path/to/cat.jpg'))
        self.assertEqual(Path('some/prefix/').rel_path_to(
                         Path('some/prefix/path/to/cat.jpg')),
                         Path('path/to/cat.jpg'))

    def test_rewrite(self):
        tmp = Path.tempdir()
        try:
            # Create original file
            orig = tmp / 'unix.txt'
            # Write some contents
            with orig.open('wb') as fp:
                fp.write(b"Some\ncontent\nin here\n")
            if issubclass(Path, PosixPath):
                orig.chmod(0o755)
            # Rewrite it in place!
            with orig.rewrite(read_newline='\n',
                              write_newline='\r\n') as (r, w):
                w.write(r.read())
            with orig.open('rb') as fp:
                self.assertEqual(fp.read(), b"Some\r\ncontent\r\nin here\r\n")
            if issubclass(Path, PosixPath):
                self.assertTrue(orig.stat().st_mode & 0o100)
        finally:
            tmp.rmtree()


class TestLists(unittest.TestCase):
    """Tests listing methods.
    """
    @classmethod
    def setUpClass(cls):
        """Builds a test hierarchy."""
        cls.tmp = Path.tempdir()
        cls.tmp.open('w', 'file').close()
        cls.tmp.open('w', 'r\xE9mi\'s thing').close()
        d = cls.tmp.mkdir('r\xE9pertoire')
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

    def compare_paths(self, root, actual, expected):
        expected = expected[issubclass(Path, PosixPath)]
        actual = set(p.path for p in actual)
        expected = set(os.path.join(root.path, f) for f in expected)
        self.assertEqual(actual, expected)

    def test_listdir(self):
        """Lists test directories."""
        self.compare_paths(self.tmp, self.tmp.listdir(),
                           (['file', 'r\xE9mi\'s thing', 'r\xE9pertoire'],
                            [b'file', b'r\xC3\xA9mi\'s thing',
                             b'r\xC3\xA9pertoire']))
        self.compare_paths(self.tmp, self.tmp.listdir('*e'),
                           (['file', 'r\xE9pertoire'],
                            [b'file', b'r\xC3\xA9pertoire']))
        self.compare_paths(self.tmp, self.tmp.listdir(lambda p: p.is_dir()),
                           (['r\xE9pertoire'], [b'r\xC3\xA9pertoire']))

        p2 = self.tmp / 'r\xE9pertoire'
        self.compare_paths(p2, p2.listdir(),
                           (['file', 'nested', 'last'],
                            [b'file', b'nested', b'last']))
        self.compare_paths(p2, p2.listdir('*e'), (['file'], [b'file']))

    def test_recursedir(self):
        """Uses recursedir to list a hierarchy."""
        expected = (['file', 'r\xE9mi\'s thing', 'r\xE9pertoire',
                     'r\xE9pertoire\\file', 'r\xE9pertoire\\last',
                     'r\xE9pertoire\\nested'],
                    [b'file', b'r\xC3\xA9mi\'s thing', b'r\xC3\xA9pertoire',
                     b'r\xC3\xA9pertoire/file', b'r\xC3\xA9pertoire/last',
                     b'r\xC3\xA9pertoire/nested'])
        self.compare_paths(self.tmp, self.tmp.recursedir(), expected)
        self.compare_paths(self.tmp, self.tmp.recursedir('*'), expected)

        self.compare_paths(self.tmp, self.tmp.recursedir('*e'),
                           (['file', 'r\xE9pertoire', 'r\xE9pertoire\\file'],
                            [b'file', b'r\xC3\xA9pertoire',
                             b'r\xC3\xA9pertoire/file']))

        self.compare_paths(self.tmp, self.tmp.recursedir(Pattern('/file')),
                           (['file'], [b'file']))
        self.compare_paths(self.tmp,
                           self.tmp.recursedir('/r\xE9pertoire/file'),
                           (['r\xE9pertoire\\file'],
                            [b'r\xC3\xA9pertoire/file']))
        self.compare_paths(self.tmp,
                           self.tmp.recursedir(Pattern('/r\xE9pertoire/file')),
                           (['r\xE9pertoire\\file'],
                            [b'r\xC3\xA9pertoire/file']))


class TestPattern2Re(unittest.TestCase):
    """Tests the pattern2re() function, used to recognize extended patterns.
    """
    def do_test_pattern(self, pattern, start, tests, interm=False):
        s, fr, ir = pattern2re(pattern)
        error = ''
        if s != start:
            error += "\n%r didn't start at %r (but %r)" % (pattern, start, s)
        if interm:
            r = ir
            suffix = " (interm=True)"
        else:
            r = fr
            suffix = ""
        for path, expected in tests:
            passed = r.search(path)
            if passed and not expected:
                error += "\n%r matched %r%s" % (pattern, path, suffix)
            elif not passed and expected:
                error += "\n%r didn't match %r%s" % (pattern, path, suffix)
        if error:
            self.fail(error)

    def test_components(self):
        """Tests how components are handled, with '*', '**', '/'."""
        self.do_test_pattern(
            # Pattern does not contain a slash: only matches the filename,
            # line fnmatch
            r'*.txt',
            '',
            [('test.txt', True),
             ('some/test.txt', True),
             ('.txt/file.png', False),
             ('not_a.txt/thing.txt.jpg', False)])
        self.do_test_pattern(
            # Pattern contains a slash: matches on the whole path
            r'/*.txt',
            '',
            [('test.txt', True),
             ('some/test.txt', False),
             ('.txt/file.png', False),
             ('not_a.txt/thing.txt.jpg', False)])
        self.do_test_pattern(
            # Note that trailing slash is ignored; do not use this...
            r'mydir/*.txt/',
            'mydir',
            [('test.txt', False),
             ('some/dir/test.txt', False),
             ('some/path/mydir/test.txt', False),
             ('mydir/thing.txt', True),
             ('.txt/file.png', False),
             ('mydir/thing.txt.jpg', False)])
        self.do_test_pattern(
            # ** will match at least one component
            r'**/mydir/*.txt',
            '',
            [('test.txt', False),
             ('some/dir/test.txt', False),
             ('path/mydir/test.txt', True),
             ('path/notmydir/test.txt', False),
             ('some/path/mydir/test.txt', True),
             ('mydir/thing.txt', False),
             ('.txt/file.png', False),
             ('mydir/thing.txt.jpg', False)])
        self.do_test_pattern('', '',
                             [('file', True), ('other/thing/here', True)])

    def test_wildcards(self):
        self.do_test_pattern(
            r'some?file*.txt',
            '',
            [('somefile.txt', False),
             ('some file.txt', True),
             ('some;filename.txt', True),
             ('wowsome file.txt', False),
             ('some filename.txt.exe', False),
             ('some/filename.txt', False),
             ('some file/name.txt', False)])
        self.do_test_pattern(
            r'some\?file\*.txt',
            '',
            [('some file*.txt', False),
             ('some?file*.txt', True),
             ('some?filename.txt', False),
             ('some?file*.txt', True)])
        self.do_test_pattern(
            r'**/file',
            '',
            [('file', False),
             ('path/file', True),
             ('path/to/file', True),
             ('not/afile', False)])
        self.do_test_pattern(
            r'path/**/file',
            'path',
            [('path/to/file', True),
             ('path/file', False),
             ('path/file', False),
             ('path/to/a/file', True),
             ('pathto/a/file', False),
             ('path/to/afile', False)])
        self.do_test_pattern(
            r'path/**',
            'path',
            [('path', False),
             ('path/file', True),
             ('path/to/file', True)])

    def test_classes(self):
        self.do_test_pattern(
            r'some[ ?a]file',
            '',
            [('someafile', True),
             ('some file', True),
             ('some?file', True),
             ('some-file', False)])
        self.do_test_pattern(
            # This one is a bit weird and not very useful but helps
            # prove that PCRE things get escaped correctly
            r'some[[:alpha:]]file',
            '',
            [('somea]file', True),
             ('some[]file', True),
             ('some:]file', True),
             ('someb]file', False),
             ('somebfile', False)])

    def test_iterm(self):
        """Tests the int_regex return value."""
        self.do_test_pattern(
            r'/usr/path/*.txt',
            'usr/path',
            [('usr', True),
             ('usr/path', True),
             ('usr/lib', False)],
            interm=True)

    def test_pattern(self):
        """Tests the high-level Pattern class."""
        for pattern in ('/usr/l*/**/*.txt', b'/usr/l*/**/*.txt'):
            pattern = Pattern(pattern)
            self.assertTrue(pattern.matches('/usr/lib/irc/test.txt'))
            self.assertTrue(pattern.matches(b'/usr/local/lib/test.txt'))
            self.assertFalse(pattern.matches('/usr/bin/test.txt'))
            self.assertTrue(pattern.may_contain_matches('/usr/lib'))
            self.assertTrue(pattern.may_contain_matches('/usr'))
            self.assertFalse(pattern.may_contain_matches(b'/usr/bin'))

            self.assertTrue(pattern.matches('usr/lib/irc/test.txt'))
            self.assertFalse(pattern.matches('smthg/usr/lib/irc/test.txt'))
            self.assertTrue(pattern.may_contain_matches('usr/lib'))
            self.assertTrue(pattern.may_contain_matches('usr'))

            self.assertTrue(pattern.matches(WindowsPath(
                'usr\\localuser\\Binaries\\readme.txt')))
            self.assertFalse(pattern.matches(WindowsPath(
                'usr\\otheruser\\Binaries\\readme.txt')))

            self.assertEqual(pattern.matches('usr\\lib\\thing\\readme.txt'),
                             issubclass(Path, WindowsPath))


class TestDictUnion(unittest.TestCase):
    def test_union(self):
        common = {'a': 1, 'b': 2}
        t1 = {'a': 3, 'c': 5}
        t2 = {'a': 4, 'd': 8}
        self.assertEqual(dict_union(common, t1), {'a': 3, 'b': 2, 'c': 5})
        self.assertEqual(dict_union(common, t2), {'a': 4, 'b': 2, 'd': 8})
        self.assertEqual(common, {'a': 1, 'b': 2})
