import ntpath
import os
import posixpath
import sys
import contextlib


PY3 = sys.version_info[0] == 3

if PY3:
    unicode = str
else:
    unicode = unicode
backend_types = (unicode, bytes)


def supports_unicode_filenames(lib):
    # Python is bugged
    return lib is ntpath

    return lib.supports_unicode_filenames


class AbstractPath(object):
    def _to_backend(self, p):
        """Converts something to the correct path representation.

        If given a Path, this will simply unpack it, if it's the correct type.
        If given the correct backend, it will return that.
        If given bytes for unicode of unicode for bytes, it will encode/decode
        with a reasonable encoding. Note that these operations can raise
        UnicodeError!
        """
        if isinstance(p, self.__class__):
            return p.path
        elif isinstance(p, self._backend):
            return p
        elif self._backend is unicode and isinstance(p, bytes):
            return p.decode(self._encoding)
        elif self._backend is bytes and isinstance(p, unicode):
            return p.encode(self._encoding)
        else:
            raise TypeError("Can't construct a %s from %r" % (
                            self.__class__.__name__, type(p)))

    def __init__(self, *parts):
        if self._lib is None:
            raise RuntimeError("Can't create an AbstractPath directly!")
        self._backend = (unicode if supports_unicode_filenames(self._lib)
                         else bytes)
        self.path = self._lib.normpath(
                self._lib.join(*[self._to_backend(p) for p in parts]))

    def __div__(self, other):
        return self.__class__(self, other)
    __truediv__ = __div__

    def __repr__(self):
        if self._backend is unicode:
            s = repr(self.path)
            if PY3:
                s = s.encode('ascii', 'backslashreplace').decode('ascii')
            if s[0] != 'u':
                s = 'u' + s
        else:
            s = repr(self.path)
            if s[0] != 'b':
                s = 'b' + s
        # Returns WindowsPath(u'C:\\somedir') or PosixPath(b'/tmp')
        # It always puts the prefix (nobody uses Python 3.2 anyway)
        return '%s(%s)' % (self.__class__.__name__, s)

    def __bytes__(self):
        if self._backend is unicode:
            return self.path.encode(self._encoding, 'replace')
        else:
            return self.path

    def __unicode__(self):
        if self._backend is bytes:
            return self.path.decode(self._encoding, 'replace')
        else:
            return self.path

    if PY3:
        __str__ = __unicode__
    else:
        __str__ = __bytes__

    def expand_user(self):
        return self.__class__(self._lib.expanduser(self.path))

    def expand_vars(self):
        return self.__class__(self._lib.expandvars(self.path))

    @property
    def parent(self):
        return self.__class__(self._lib.dirname(self.path))

    @property
    def name(self):
        return self._lib.basename(self.path)

    @property
    def unicodename(self):
        n = self._lib.basename(self.path)
        if self._backend is unicode:
            return n
        else:
            return n.decode(self._encoding, 'replace')

    @property
    def stem(self):
        return self._lib.splitext(self.name)[0]

    @property
    def ext(self):
        return self._lib.splitext(self)[1]

    def split_root(self):
        if hasattr(self._lib, 'splitunc'):
            root, rest = self._lib.splitunc(self.path)
            if root:
                if rest.startswith(self._lib.sep):
                    root += self._lib.sep
                    rest = rest[1:]
                return self.__class__(root), self.__class__(rest)
        root, rest = self._lib.splitdrive(self.path)
        if root:
            if rest.startswith(self._lib.sep):
                root += self._lib.sep
                rest = rest[1:]
            return self.__class__(root), self.__class__(rest)
        if self.path.startswith(self._lib.sep):
            return self.__class__(self._lib.sep), self.__class__(rest[1:])
        return self.__class__(''), self

    @property
    def root(self):
        return self.split_root()[0]

    @property
    def components(self):
        root, loc = self.split_root()
        components = loc.split(self._lib.sep)
        if root:
            components = [root] + components
        return components

    def ancestor(self, n):
        p = self.path
        for i in range(n):
            p = p.parent
        return self.__class__(p)

    def norm_case(self):
        return self.__class__(self._lib.normcase(self.path))

    @property
    def is_absolute(self):
        return bool(self.root)


class WindowsPath(AbstractPath):
    _lib = ntpath
    _encoding = 'windows-1252'


class PosixPath(AbstractPath):
    _lib = posixpath
    _encoding = 'utf-8'


DefaultAbstractPath = WindowsPath if os.name == 'nt' else PosixPath


class Path(DefaultAbstractPath):
    @property
    def _encoding(self):
        return sys.getfilesystemencoding()

    @classmethod
    def cwd(cls):
        return cls(os.getcwd())

    def chdir(self):
        os.chdir(self.path)

    @contextlib.contextmanager
    def with_chdir(self):
        previous_dir = self.cwd()
        self.chdir()
        try:
            yield
        finally:
            previous_dir.chdir()

    def absolute(self):
        return self.__class__(self._lib.abspath(self.path))

    def relative(self):
        return self.cwd().rel_path_to(self)

    def rel_path_to(self, dest):
        orig = self.absolute()
        dest = self._to_backend(dest).absolute()

        orig_list = orig.norm_case().components
        dest_list = dest.components

        for i, (orig_part, dest_part) in enumerate(zip(orig_list, dest_list)):
            if orig_part != self._lib.normcase(dest_part):
                return self.__class__(dest_list[i:])
