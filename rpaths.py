import contextlib
import ntpath
import os
import posixpath
import shutil
import sys
import tempfile


PY3 = sys.version_info[0] == 3

if PY3:
    unicode = str
else:
    unicode = unicode
backend_types = (unicode, bytes)


def supports_unicode_filenames(lib):
    # Python is bugged; lib.supports_unicode_filenames is wrong
    return lib is ntpath


class AbstractPath(object):
    def _to_backend(self, p):
        """Converts something to the correct path representation.

        If given a Path, this will simply unpack it, if it's the correct type.
        If given the correct backend, it will return that.
        If given bytes for unicode of unicode for bytes, it will encode/decode
        with a reasonable encoding. Note that these operations can raise
        UnicodeError!
        """
        if isinstance(p, self._cmp_base):
            return p.path
        elif isinstance(p, self._backend):
            return p
        elif self._backend is unicode and isinstance(p, bytes):
            return p.decode(self._encoding)
        elif self._backend is bytes and isinstance(p, unicode):
            return p.encode(self._encoding,
                            'surrogateescape' if PY3 else 'strict')
        else:
            raise TypeError("Can't construct a %s from %r" % (
                            self.__class__.__name__, type(p)))

    def __init__(self, *parts):
        if self._lib is None:  # pragma: no cover
            raise RuntimeError("Can't create an AbstractPath directly!")
        self._backend = (unicode if supports_unicode_filenames(self._lib)
                         else bytes)
        self._sep = self._lib.sep
        if self._backend is unicode and isinstance(self._sep, bytes):
            self._sep = self._sep.decode('ascii')
        elif self._backend is bytes and isinstance(self._sep, unicode):
            self._sep = self._sep.encode('ascii')
        self.path = self._lib.normpath(
                self._lib.join(*[self._to_backend(p) for p in parts]))

    def __div__(self, other):
        return self.__class__(self, other)
    __truediv__ = __div__

    def __eq__(self, other):
        return (self._lib.normcase(self.path) ==
                self._lib.normcase(self._to_backend(other)))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.path)

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
        p = self._lib.dirname(self.path)
        p = self.__class__(p)
        return p

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
        return self._lib.splitext(self.path)[1]

    def split_root(self):
        if not PY3 and hasattr(self._lib, 'splitunc'):
            root, rest = self._lib.splitunc(self.path)
            if root:
                if rest.startswith(self._sep):
                    root += self._sep
                    rest = rest[1:]
                return self.__class__(root), self.__class__(rest)
        root, rest = self._lib.splitdrive(self.path)
        if root:
            if rest.startswith(self._sep):
                root += self._sep
                rest = rest[1:]
            return self.__class__(root), self.__class__(rest)
        if self.path.startswith(self._sep):
            return self.__class__(self._sep), self.__class__(rest[1:])
        return self.__class__(''), self

    @property
    def root(self):
        return self.split_root()[0]

    @property
    def components(self):
        root, loc = self.split_root()
        components = loc.split(self._sep)
        if root:
            components = [root] + components
        return components

    def ancestor(self, n):
        p = self
        for i in range(n):
            p = p.parent
        return p

    def norm_case(self):
        return self.__class__(self._lib.normcase(self.path))

    @property
    def is_absolute(self):
        return self.root.path != self._to_backend('.')


class WindowsPath(AbstractPath):
    _lib = ntpath
    _encoding = 'windows-1252'
WindowsPath._cmp_base = WindowsPath


class PosixPath(AbstractPath):
    _lib = posixpath
    _encoding = 'utf-8'
PosixPath._cmp_base = PosixPath


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
    def in_dir(self):
        previous_dir = self.cwd()
        self.chdir()
        try:
            yield
        finally:
            previous_dir.chdir()

    @classmethod
    def tempfile(cls, suffix='', prefix=None, dir=None, text=False):
        if prefix is None:
            prefix = tempfile.template
        fd, filename = tempfile.mkstemp(suffix, prefix, dir, text)
        return fd, cls(filename).absolute()

    @classmethod
    def tempdir(cls, suffix='', prefix=None, dir=None):
        if prefix is None:
            prefix = tempfile.template
        dirname = tempfile.mkdtemp(suffix, prefix, dir)
        return cls(dirname).absolute()

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
                # TODO : Work in progress

    def resolve(self):
        return self.__class__(self._lib.realpath(self.path))

    def listdir(self):
        return [self / self.__class__(p) for p in os.listdir(self.path)]

    def recursedir(self, top_down=True):
        return self._recursedir(top_down=top_down, seen=set())

    def _recursedir(self, top_down, seen):
        if not self.is_dir():
            raise ValueError("recursedir() called on non-directory %s" % self)
        real_dir = self.resolve()
        if real_dir in seen:
            return
        seen.add(real_dir)
        for child in self.listdir():
            is_dir = child.is_dir()
            if is_dir and not top_down:
                for grandkid in child._recursedir(top_down, seen):
                    yield grandkid
            yield child
            if is_dir and top_down:
                for grandkid in child._recursedir(top_down, seen):
                    yield grandkid

    def exists(self):
        return self._lib.exists(self.path)

    def lexists(self):
        return self._lib.lexists(self.path)

    def is_file(self):
        return self._lib.isfile(self.path)

    def is_dir(self):
        return self._lib.isdir(self.path)

    def is_link(self):
        return self._lib.islink(self.path)

    def is_mount(self):
        return self._lib.ismount(self.path)

    def atime(self):
        return self._lib.atime(self.path)

    def ctime(self):
        return self._lib.ctime(self.path)

    def mtime(self):
        return self._lib.mtime(self.path)

    def size(self):
        return self._lib.getsize(self.path)

    if hasattr(os.path, 'samefile'):
        def same_file(self, other):
            return self._lib.samefile(self.path, self._to_backend(other))

    def stat(self):
        return os.stat(self.path)

    def lstat(self):
        return os.lstat(self.path)

    if hasattr(os, 'statvfs'):
        def statvfs(self):
            return os.statvfs(self.path)

    if hasattr(os, 'chmod'):
        def chmod(self, mode):
            return os.chmod(self.path, mode)

    if hasattr(os, 'chown'):
        def chown(self, uid, gid):
            return os.chown(self.path, uid, gid)

    def mkdir(self, name=None, parents=False, mode=0o777):
        if name is not None:
            return (self / name).mkdir(parents=parents, mode=mode)
        if self.exists():
            return
        if parents:
            os.makedirs(self.path, mode)
        else:
            os.mkdir(self.path, mode)
        return self

    def rmdir(self, parents=False):
        if parents:
            os.removedirs(self.path)
        else:
            os.rmdir(self.path)

    def remove(self):
        os.remove(self.path)

    def rename(self, new, parents=False):
        if parents:
            os.renames(self.path, self._to_backend(new))
        else:
            os.rename(self.path, self._to_backend(new))

    if hasattr(os, 'link'):
        def hardlink(self, newpath):
            os.link(self.path, self._to_backend(newpath))

    if hasattr(os, 'symlink'):
        def symlink(self, target):
            os.symlink(self._to_backend(target), self.path)

    if hasattr(os, 'readlink'):
        def read_link(self, absolute=False):
            p = self.__class__(os.readlink(self))
            if absolute:
                return p.absolute()
            else:
                return p

    # TODO : shutil copy* stuff

    def rmtree(self, ignore_errors=False):
        shutil.rmtree(self.path, ignore_errors)

    def open(self, mode='r', name=None):
        if name is not None:
            return open((self / name).path, mode)
        else:
            return open(self.path, mode)
