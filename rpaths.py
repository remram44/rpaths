from __future__ import unicode_literals

import contextlib
import functools
import io
import ntpath
import os
import posixpath
import re
import shutil
import sys
import tempfile


__all__ = ["unicode", "Path", "PY3", "PosixPath", "WindowsPath"]

__version__ = '0.13'


PY3 = sys.version_info[0] == 3

if PY3:
    unicode = str
else:
    unicode = unicode
backend_types = (unicode, bytes)


MAX_CACHE = 128
if hasattr(functools, 'lru_cache'):
    memoize1 = functools.lru_cache(MAX_CACHE)
else:
    def memoize1(f):
        _cache = {}

        @functools.wraps(f)
        def wrapped(arg):
            if arg in _cache:
                return _cache[arg]
            else:
                res = f(arg)
                if len(_cache) > MAX_CACHE:
                    _cache.clear()
                _cache[arg] = res
                return res

        return wrapped


def supports_unicode_filenames(lib):
    # Python is bugged; lib.supports_unicode_filenames is wrong
    return lib is ntpath


def dict_union(*dcts):
    dct = {}
    for dct2 in dcts:
        dct.update(dct2)
    return dct


class AbstractPath(object):
    """An abstract representation of a path.

    This represents a path on a system that may not be the current one. It
    doesn't provide any way to actually interact with the local file system.
    """
    _lib = None

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
        """Creates a path from one or more components.
        """
        if self._lib is None:  # pragma: no cover
            raise RuntimeError("Can't create an AbstractPath directly!")
        self._backend = (unicode if supports_unicode_filenames(self._lib)
                         else bytes)
        self._sep = self._lib.sep
        if self._backend is unicode and isinstance(self._sep, bytes):
            self._sep = self._sep.decode('ascii')
        elif self._backend is bytes and isinstance(self._sep, unicode):
            self._sep = self._sep.encode('ascii')
        self.path = self._normpath(
            self._lib.join(*[self._to_backend(p) for p in parts]))

    @classmethod
    def _normpath(cls, p):
        """This gets a pathname into the proper form it will be stored as.
        """
        return cls._lib.normpath(p)

    @classmethod
    def _normcase(cls, p):
        """This gets a pathname into the proper form for equality testing.
        """
        return cls._lib.normcase(p)

    def __div__(self, other):
        """Joins two paths.
        """
        return self.__class__(self, other)
    __truediv__ = __div__

    def __add__(self, other):
        """Adds a suffix to some path (for example, '.bak').
        """
        if not isinstance(other, backend_types):
            raise TypeError("+ operator expects a str or bytes object, "
                            "got %r" % type(other))
        other = self._to_backend(other)
        if self._to_backend('/') in other or self._sep in other:
            raise ValueError("Can't add separators to filename with +, use /")
        return self.__class__(self.path + other)

    def __eq__(self, other):
        """Compares two paths.

        This will ignore the case on systems where it is not relevant. Note
        that if two paths are equal, they represent the same file, but the
        opposite might not be true.
        """
        try:
            other = self._to_backend(other)
        except TypeError:
            return NotImplemented
        else:
            return (self._normcase(self.path) == self._normcase(other))

    # functools.total_ordering is broken (cf http://bugs.python.org/issue10042)
    # so we don't use it

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        """Compares two paths.

        This will ignore the case on systems where it is not relevant.
        """
        try:
            other = self._to_backend(other)
        except TypeError:
            return NotImplemented
        else:
            return self._normcase(self.path) < self._normcase(other)

    def __le__(self, other):
        """Compares two paths.

        This will ignore the case on systems where it is not relevant.
        """
        try:
            other = self._to_backend(other)
        except TypeError:
            return NotImplemented
        else:
            return self._normcase(self.path) <= self._normcase(other)

    def __gt__(self, other):
        """Compares two paths.

        This will ignore the case on systems where it is not relevant.
        """
        try:
            other = self._to_backend(other)
        except TypeError:
            return NotImplemented
        else:
            return self._normcase(self.path) > self._normcase(other)

    def __ge__(self, other):
        """Compares two paths.

        This will ignore the case on systems where it is not relevant.
        """
        try:
            other = self._to_backend(other)
        except TypeError:
            return NotImplemented
        else:
            return self._normcase(self.path) >= self._normcase(other)

    def __hash__(self):
        return hash(self._normcase(self.path))

    def __repr__(self):
        """Prints a representation of the path.

        Returns WindowsPath(u'C:\\somedir') or PosixPath(b'/tmp').
        It always puts the 'b' or 'u' prefix (nobody likes Python 3.2 anyway).
        """
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
        return '%s(%s)' % (self.__class__.__name__, s)

    def __bytes__(self):
        """Gives a bytestring version of the path.

        Note that if the path is unicode and contains international characters,
        this function will not raise, but the pathname will not be valid. It is
        meant for display purposes only; use the ``path`` attribute for a
        correct path (which might be bytes or unicode, depending on the
        system).
        """
        if self._backend is unicode:
            return self.path.encode(self._encoding, 'replace')
        else:
            return self.path

    def __unicode__(self):
        """Gives a unicode version of the path.

        Note that if the path is binary and contains invalid byte sequences,
        this function will not raise, but the pathname will not be valid. It is
        meant for display purposes only; use the ``path`` attribute for a
        correct path (which might be bytes or unicode, depending on the
        system).
        """
        if self._backend is bytes:
            if PY3:
                return self.path.decode(self._encoding, 'surrogateescape')
            else:
                return self.path.decode(self._encoding, 'replace')
        else:
            return self.path

    if PY3:
        __str__ = __unicode__
    else:
        __str__ = __bytes__

    def expand_user(self):
        """Replaces ``~`` or ``~user`` by that user's home directory.
        """
        return self.__class__(self._lib.expanduser(self.path))

    def expand_vars(self):
        """Expands environment variables in the path.

        They might be of the form ``$name`` or ``${name}``; references to
        non-existing variables are kept unchanged.
        """
        return self.__class__(self._lib.expandvars(self.path))

    @property
    def parent(self):
        """The parent directory of this path.
        """
        p = self._lib.dirname(self.path)
        p = self.__class__(p)
        return p

    @property
    def name(self):
        """The name of this path, i.e. the final component without directories.
        """
        return self._lib.basename(self.path)

    @property
    def unicodename(self):
        """The name of this path as unicode.
        """
        n = self._lib.basename(self.path)
        if self._backend is unicode:
            return n
        else:
            return n.decode(self._encoding, 'replace')

    @property
    def stem(self):
        """The name of this path without the extension.
        """
        return self._lib.splitext(self.name)[0]

    @property
    def ext(self):
        """The extension of this path.
        """
        return self._lib.splitext(self.path)[1]

    def split_root(self):
        """Splits this path into a pair (drive, location).

        Note that, because all paths are normalized, a root of ``'.'`` will be
        returned for relative paths.
        """
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
        """The root of this path.

        This will be either a root (with optionally a drive name or UNC share)
        or ``'.'`` for relative paths.
        """
        return self.split_root()[0]

    @property
    def components(self):
        """Splits this path into its components.

        The first component will be the root if this path is relative, then
        each component leading to the filename.
        """
        return [self.__class__(p) for p in self._components()]

    def _components(self):
        root, loc = self.split_root()
        if root.path != self._to_backend('.'):
            components = [root.path]
        else:
            components = []
        if loc.path != self._to_backend('.'):
            components.extend(loc.path.split(self._sep))
        return components

    def ancestor(self, n):
        """Goes up `n` directories.
        """
        p = self
        for i in range(n):
            p = p.parent
        return p

    def norm_case(self):
        """Removes the case if this flavor of paths is case insensitive.
        """
        return self.__class__(self._normcase(self.path))

    @property
    def is_absolute(self):
        """Indicates whether this path is absolute or relative.
        """
        return self.root.path != self._to_backend('.')

    def rel_path_to(self, dest):
        """Builds a relative path leading from this one to the given `dest`.

        Note that these paths might be both relative, in which case they'll be
        assumed to start from the same directory.
        """
        dest = self.__class__(dest)

        orig_list = self.norm_case()._components()
        dest_list = dest._components()

        i = -1
        for i, (orig_part, dest_part) in enumerate(zip(orig_list, dest_list)):
            if orig_part != self._normcase(dest_part):
                up = ['..'] * (len(orig_list) - i)
                return self.__class__(*(up + dest_list[i:]))

        if len(orig_list) <= len(dest_list):
            if len(dest_list) > i + 1:
                return self.__class__(*dest_list[i + 1:])
            else:
                return self.__class__('')
        else:
            up = ['..'] * (len(orig_list) - i - 1)
            return self.__class__(*up)

    def lies_under(self, prefix):
        """Indicates if the `prefix` is a parent of this path.
        """
        orig_list = self.norm_case()._components()
        pref_list = self.__class__(prefix).norm_case()._components()

        return (len(orig_list) >= len(pref_list) and
                orig_list[:len(pref_list)] == pref_list)


class WindowsPath(AbstractPath):
    """An abstract representation of a Windows path.

    It is safe to build and use objects of this class even when not running on
    Windows.
    """
    _lib = ntpath
    _encoding = 'windows-1252'


WindowsPath._cmp_base = WindowsPath


class PosixPath(AbstractPath):
    """An abstract representation of a POSIX path.

    It is safe to build and use objects of this class even when running on
    Windows.
    """
    _lib = posixpath
    _encoding = 'utf-8'


PosixPath._cmp_base = PosixPath


DefaultAbstractPath = WindowsPath if os.name == 'nt' else PosixPath


try:
    import unicodedata
except ImportError:
    pass
else:
    class MacOSPath(PosixPath):
        """An abstract representation of a path on Mac OS X.

        The filesystem on Mac OS X (HFS) normalizes unicode sequences (NFC).
        """
        @classmethod
        def _normpath(cls, p):
            return unicodedata.normalize('NFC',
                                         p.decode('utf-8')).encode('utf-8')

    if sys.platform == 'darwin':
        DefaultAbstractPath = MacOSPath


class Path(DefaultAbstractPath):
    """A concrete representation of an actual path on this system.

    This extends either :class:`~rpaths.WindowsPath` or
    :class:`~rpaths.PosixPath` depending on the current system. It adds
    concrete filesystem operations.
    """
    @property
    def _encoding(self):
        return sys.getfilesystemencoding()

    @classmethod
    def cwd(cls):
        """Returns the current directory.
        """
        return cls(os.getcwd())

    def chdir(self):
        """Changes the current directory to this path.
        """
        os.chdir(self.path)

    @contextlib.contextmanager
    def in_dir(self):
        """Context manager that changes to this directory then changes back.
        """
        previous_dir = self.cwd()
        self.chdir()
        try:
            yield
        finally:
            previous_dir.chdir()

    @classmethod
    def tempfile(cls, suffix='', prefix=None, dir=None, text=False):
        """Returns a new temporary file.

        The return value is a pair (fd, path) where fd is the file descriptor
        returned by :func:`os.open`, and path is a :class:`~rpaths.Path` to it.

        :param suffix: If specified, the file name will end with that suffix,
            otherwise there will be no suffix.

        :param prefix: Is specified, the file name will begin with that prefix,
            otherwise a default prefix is used.

        :param dir: If specified, the file will be created in that directory,
            otherwise a default directory is used.

        :param text: If true, the file is opened in text mode. Else (the
            default) the file is opened in binary mode.  On some operating
            systems, this makes no difference.

        The file is readable and writable only by the creating user ID.
        If the operating system uses permission bits to indicate whether a
        file is executable, the file is executable by no one. The file
        descriptor is not inherited by children of this process.

        The caller is responsible for deleting the file when done with it.
        """
        if prefix is None:
            prefix = tempfile.template
        if dir is not None:
            # Note that this is not safe on Python 2
            # There is no work around, apart from not using the tempfile module
            dir = str(Path(dir))
        fd, filename = tempfile.mkstemp(suffix, prefix, dir, text)
        return fd, cls(filename).absolute()

    @classmethod
    def tempdir(cls, suffix='', prefix=None, dir=None):
        """Returns a new temporary directory.

        Arguments are as for :meth:`~rpaths.Path.tempfile`, except that the
        `text` argument is not accepted.

        The directory is readable, writable, and searchable only by the
        creating user.

        The caller is responsible for deleting the directory when done with it.
        """
        if prefix is None:
            prefix = tempfile.template
        if dir is not None:
            # Note that this is not safe on Python 2
            # There is no work around, apart from not using the tempfile module
            dir = str(Path(dir))
        dirname = tempfile.mkdtemp(suffix, prefix, dir)
        return cls(dirname).absolute()

    def absolute(self):
        """Returns a normalized absolutized version of the path.
        """
        return self.__class__(self._lib.abspath(self.path))

    def rel_path_to(self, dest):
        """Builds a relative path leading from this one to another.

        Note that these paths might be both relative, in which case they'll be
        assumed to be considered starting from the same directory.

        Contrary to :class:`~rpaths.AbstractPath`'s version, this will also
        work if one path is relative and the other absolute.
        """
        return super(Path, self.absolute()).rel_path_to(Path(dest).absolute())

    def relative(self):
        """Builds a relative version of this path from the current directory.

        This is the same as ``Path.cwd().rel_path_to(thispath)``.
        """
        return self.cwd().rel_path_to(self)

    def resolve(self):
        """Expands the symbolic links in the path.
        """
        return self.__class__(self._lib.realpath(self.path))

    def listdir(self, pattern=None):
        """Returns a list of all the files in this directory.

        The special entries ``'.'`` and ``'..'`` will not be returned.

        :param pattern: A pattern to match directory entries against.
        :type pattern: NoneType | Callable | Pattern | unicode | bytes
        """
        files = [self / self.__class__(p) for p in os.listdir(self.path)]
        if pattern is None:
            pass
        elif callable(pattern):
            files = filter(pattern, files)
        else:
            if isinstance(pattern, backend_types):
                if isinstance(pattern, bytes):
                    pattern = pattern.decode(self._encoding, 'replace')
                start, full_re, _int_re = pattern2re(pattern)
            elif isinstance(pattern, Pattern):
                start, full_re = pattern.start_dir, pattern.full_regex
            else:
                raise TypeError("listdir() expects pattern to be a callable, "
                                "a regular expression or a string pattern, "
                                "got %r" % type(pattern))
            # If pattern contains slashes (other than first and last chars),
            # listdir() will never match anything
            if start:
                return []
            files = [f for f in files if full_re.search(f.unicodename)]
        return files

    def recursedir(self, pattern=None, top_down=True, follow_links=False,
                   handle_errors=None):
        """Recursively lists all files under this directory.

        :param pattern: An extended patterns, where:

            * a slash '/' always represents the path separator
            * a backslash '\' escapes other special characters
            * an initial slash '/' anchors the match at the beginning of the
              (relative) path
            * a trailing '/' suffix is removed
            * an asterisk '*'  matches a sequence of any length (including 0)
              of any characters (except the path separator)
            * a '?' matches exactly one character (except the path separator)
            * '[abc]' matches characters 'a', 'b' or 'c'
            * two asterisks '**' matches one or more path components (might
              match '/' characters)
        :type pattern: NoneType | Callable | Pattern | unicode | bytes

        :param follow_links: If False, symbolic links will not be followed (the
            default). Else, they will be followed, but directories reached
            through different names will *not* be listed multiple times.

        :param handle_errors: Can be set to a callback that will be called when
            an error is encountered while accessing the filesystem (such as a
            permission issue). If set to None (the default), exceptions will be
            propagated.
        """
        if not self.is_dir():
            raise ValueError("recursedir() called on non-directory %s" % self)

        start = ''
        int_pattern = None
        if pattern is None:
            pattern = lambda p: True
        elif callable(pattern):
            pass
        else:
            if isinstance(pattern, backend_types):
                if isinstance(pattern, bytes):
                    pattern = pattern.decode(self._encoding, 'replace')
                start, full_re, int_re = pattern2re(pattern)
            elif isinstance(pattern, Pattern):
                start, full_re, int_re = \
                    pattern.start_dir, pattern.full_regex, pattern.int_regex
            else:
                raise TypeError("recursedir() expects pattern to be a "
                                "callable, a regular expression or a string "
                                "pattern, got %r" % type(pattern))
            if self._lib.sep != '/':
                pattern = lambda p: full_re.search(
                    unicode(p).replace(self._lib.sep, '/'))
                if int_re is not None:
                    int_pattern = lambda p: int_re.search(
                        unicode(p).replace(self._lib.sep, '/'))
            else:
                pattern = lambda p: full_re.search(unicode(p))
                if int_re is not None:
                    int_pattern = lambda p: int_re.search(unicode(p))
        if not start:
            path = self
        else:
            path = self / start
            if not path.exists():
                return []
            elif not path.is_dir():
                return [path]
        return path._recursedir(pattern=pattern, int_pattern=int_pattern,
                                top_down=top_down, seen=set(),
                                path=self.__class__(start),
                                follow_links=follow_links,
                                handle_errors=handle_errors)

    def _recursedir(self, pattern, int_pattern, top_down, seen, path,
                    follow_links=False, handle_errors=None):
        real_dir = self.resolve()
        if real_dir in seen:
            return
        seen.add(real_dir)
        try:
            dir_list = os.listdir(self.path)
        except OSError:
            if handle_errors is not None:
                handle_errors(self.path)
                return
            raise
        for child in dir_list:
            newpath = path / child
            child = self / child
            is_dir = child.is_dir() and (not child.is_link() or follow_links)
            # Fast failing thanks to int_pattern here: if we don't match
            # int_pattern, don't try inner files either
            matches_pattern = pattern(newpath)
            if (not matches_pattern and
                    int_pattern is not None and not int_pattern(newpath)):
                continue
            if is_dir and not top_down:
                for grandkid in child._recursedir(pattern, int_pattern,
                                                  top_down, seen, newpath,
                                                  follow_links, handle_errors):
                    yield grandkid
            if matches_pattern:
                yield child
            if is_dir and top_down:
                for grandkid in child._recursedir(pattern, int_pattern,
                                                  top_down, seen, newpath,
                                                  follow_links, handle_errors):
                    yield grandkid

    def exists(self):
        """True if the file exists, except for broken symlinks where it's
        False.
        """
        return self._lib.exists(self.path)

    def lexists(self):
        """True if the file exists, even if it's a broken symbolic link.
        """
        return self._lib.lexists(self.path)

    def is_file(self):
        """True if this file exists and is a regular file.
        """
        return self._lib.isfile(self.path)

    def is_dir(self):
        """True if this file exists and is a directory.
        """
        return self._lib.isdir(self.path)

    def is_link(self):
        """True if this file exists and is a symbolic link.
        """
        return self._lib.islink(self.path)

    def is_mount(self):
        """True if this file is a mount point.
        """
        return self._lib.ismount(self.path)

    def atime(self):
        """Returns the time of last access to this path.

        This returns a number of seconds since the epoch.
        """
        return self._lib.getatime(self.path)

    def ctime(self):
        """Returns the ctime of this path.

        On some systems, this is the time of last metadata change, and on
        others (like Windows), it is the creation time for path. In any case,
        it is a number of seconds since the epoch.
        """
        return self._lib.getctime(self.path)

    def mtime(self):
        """Returns the time of last modification of this path.

        This returns a number of seconds since the epoch.
        """
        return self._lib.getmtime(self.path)

    def size(self):
        """Returns the size, in bytes, of the file.
        """
        return self._lib.getsize(self.path)

    if hasattr(os.path, 'samefile'):
        def same_file(self, other):
            """Returns True if both paths refer to the same file or directory.

            In particular, this identifies hard links.
            """
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
            """Changes the mode of the path to the given numeric `mode`.
            """
            return os.chmod(self.path, mode)

    if hasattr(os, 'chown'):
        def chown(self, uid=-1, gid=-1):
            """Changes the owner and group id of the path.
            """
            return os.chown(self.path, uid, gid)

    def mkdir(self, name=None, parents=False, mode=0o777):
        """Creates that directory, or a directory under this one.

        ``path.mkdir(name)`` is a shortcut for ``(path/name).mkdir()``.

        :param name: Path component to append to this path before creating the
            directory.

        :param parents: If True, missing directories leading to the path will
            be created too, recursively. If False (the default), the parent of
            that path needs to exist already.

        :param mode: Permissions associated with the directory on creation,
            without race conditions.
        """
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
        """Removes this directory, provided it is empty.

        Use :func:`~rpaths.Path.rmtree` if it might still contain files.

        :param parents: If set to True, it will also destroy every empty
            directory above it until an error is encountered.
        """
        if parents:
            os.removedirs(self.path)
        else:
            os.rmdir(self.path)

    def remove(self):
        """Removes this file.
        """
        os.remove(self.path)

    def rename(self, new, parents=False):
        """Renames this path to the given new location.

        :param new: New path where to move this one.

        :param parents: If set to True, it will create the parent directories
            of the target if they don't exist.
        """
        if parents:
            os.renames(self.path, self._to_backend(new))
        else:
            os.rename(self.path, self._to_backend(new))

    if hasattr(os, 'link'):
        def hardlink(self, newpath):
            """Creates a hard link to this path at the given `newpath`.
            """
            os.link(self.path, self._to_backend(newpath))

    if hasattr(os, 'symlink'):
        def symlink(self, target):
            """Create a symbolic link here, pointing to the given `target`.
            """
            os.symlink(self._to_backend(target), self.path)

    if hasattr(os, 'readlink'):
        def read_link(self, absolute=False):
            """Returns the path this link points to.

            If `absolute` is True, the target is made absolute.
            """
            p = self.__class__(os.readlink(self.path))
            if absolute:
                return (self.parent / p).absolute()
            else:
                return p

    def copyfile(self, target):
        """Copies this file to the given `target` location.
        """
        shutil.copyfile(self.path, self._to_backend(target))

    def copymode(self, target):
        """Copies the mode of this file on the `target` file.

        The owner is not copied.
        """
        shutil.copymode(self.path, self._to_backend(target))

    def copystat(self, target):
        """Copies the permissions, times and flags from this to the `target`.

        The owner is not copied.
        """
        shutil.copystat(self.path, self._to_backend(target))

    def copy(self, target):
        """Copies this file the `target`, which might be a directory.

        The permissions are copied.
        """
        shutil.copy(self.path, self._to_backend(target))

    def copytree(self, target, symlinks=False):
        """Recursively copies this directory to the `target` location.

        The permissions and times are copied (like
        :meth:`~rpaths.Path.copystat`).

        If the optional `symlinks` flag is true, symbolic links in the source
        tree result in symbolic links in the destination tree; if it is false,
        the contents of the files pointed to by symbolic links are copied.
        """
        shutil.copytree(self.path, self._to_backend(target), symlinks)

    def rmtree(self, ignore_errors=False):
        """Deletes an entire directory.

        If ignore_errors is True, failed removals will be ignored; else,
        an exception will be raised.
        """
        shutil.rmtree(self.path, ignore_errors)

    def move(self, target):
        """Recursively moves a file or directory to the given target location.
        """
        shutil.move(self.path, self._to_backend(target))

    def open(self, mode='r', name=None, **kwargs):
        """Opens this file, or a file under this directory.

        ``path.open(mode, name)`` is a shortcut for ``(path/name).open(mode)``.

        Note that this uses :func:`io.open()` which behaves differently from
        :func:`open()` on Python 2; see the appropriate documentation.

        :param name: Path component to append to this path before opening the
            file.
        """
        if name is not None:
            return io.open((self / name).path, mode=mode, **kwargs)
        else:
            return io.open(self.path, mode=mode, **kwargs)

    @contextlib.contextmanager
    def rewrite(self, mode='r', name=None, temp=None, tempext='~', **kwargs):
        r"""Replaces this file with new content.

        This context manager gives you two file objects, (r, w), where r is
        readable and has the current content of the file, and w is writable
        and will replace the file at the end of the context (unless an
        exception is raised, in which case it is rolled back).

        Keyword arguments will be used for both files, unless they are prefixed
        with ``read_`` or ``write_``. For instance::

            with Path('test.txt').rewrite(read_newline='\n',
                                          write_newline='\r\n') as (r, w):
                w.write(r.read())

        :param name: Path component to append to this path before opening the
            file.

        :param temp: Temporary file name to write, and then move over this one.
            By default it's this filename with a ``~`` suffix.

        :param tempext: Extension to add to this file to get the temporary file
            to write then move over this one. Defaults to ``~``.
        """
        if name is not None:
            pathr = self / name
        else:
            pathr = self
        for m in 'war+':
            mode = mode.replace(m, '')

        # Build options
        common_kwargs = {}
        readable_kwargs = {}
        writable_kwargs = {}
        for key, value in kwargs.items():
            if key.startswith('read_'):
                readable_kwargs[key[5:]] = value
            elif key.startswith('write_'):
                writable_kwargs[key[6:]] = value
            else:
                common_kwargs[key] = value
        readable_kwargs = dict_union(common_kwargs, readable_kwargs)
        writable_kwargs = dict_union(common_kwargs, writable_kwargs)

        with pathr.open('r' + mode, **readable_kwargs) as readable:
            if temp is not None:
                pathw = Path(temp)
            else:
                pathw = pathr + tempext
            try:
                pathw.remove()
            except OSError:
                pass
            writable = pathw.open('w' + mode, **writable_kwargs)
            try:
                yield readable, writable
            except Exception:
                # Problem, delete writable
                writable.close()
                pathw.remove()
                raise
            else:
                writable.close()
        # Alright, replace
        pathr.copymode(pathw)
        pathr.remove()
        pathw.rename(pathr)


class Pattern(object):
    """A pattern that paths can be matched against.

    You can check if a filename matches this pattern by using `matches()`, or
    pass it to the `Path.listdir` and `Path.recursedir` methods.

    `may_contain_matches()` is a special method which you can feed directories
    to; if it returns False, no path under that one will match the pattern.

    >>> pattern = Pattern('/usr/l*/**.so')
    >>> pattern.matches('/usr/local/irc/mod_user.so')
    True
    >>> pattern.matches('/usr/bin/thing.so')
    False
    >>> pattern.may_contain_matches('/usr')
    True
    >>> pattern.may_contain_matches('/usr/lib')
    True
    >>> pattern.may_contain_matches('/usr/bin')
    False
    """
    def __init__(self, pattern):
        if isinstance(pattern, bytes):
            pattern = pattern.decode(sys.getfilesystemencoding())
        self.start_dir, self.full_regex, self.int_regex = pattern2re(pattern)

    @staticmethod
    def _prepare_path(path):
        # Here we want to force the use of replacement characters.
        # The __unicode__ implementation might use 'surrogateescape'
        replace = False
        if isinstance(path, AbstractPath):
            replace = path._lib.sep if path._lib.sep != '/' else None
            path = path.path
        else:
            replace = Path._lib.sep if Path._lib.sep != '/' else None
        if isinstance(path, bytes):
            path = path.decode(sys.getfilesystemencoding(), 'replace')
        elif not isinstance(path, unicode):
            raise TypeError("Expected a path, got %r" % type(path))

        if path.startswith('/'):
            path = path[1:]

        if replace is not None:
            path = path.replace(replace, '/')

        return path

    def matches(self, path):
        """Tests if the given path matches the pattern.

        Note that the unicode translation of the patch is matched, so
        replacement characters might have been added.
        """
        path = self._prepare_path(path)
        return self.full_regex.search(path) is not None

    def may_contain_matches(self, path):
        """Tests whether it's possible for paths under the given one to match.

        If this method returns None, no path under the given one will match the
        pattern.
        """
        path = self._prepare_path(path)
        return self.int_regex.search(path) is not None


no_special_chars = re.compile(r'^(?:[^\\*?\[\]]|\\.)*$')


def patterncomp2re(component):
    if component == '**':
        return '.*'
    i, n = 0, len(component)
    regex = ''
    while i < n:
        c = component[i]
        if c == '\\':
            i += 1
            if i < n:
                regex += re.escape(component[i])
        elif c == '*':
            regex += '[^/]*'
        elif c == '?':
            regex += '[^/]'
        elif c == '[':
            i += 1
            regex += '['
            c = component[i]
            while c != ']':
                if c == '/':
                    raise ValueError("Slashes not accepted in [] classes")
                regex += re.escape(c)
                i += 1
                c = component[i]
            regex += ']'
        else:
            regex += re.escape(c)
        i += 1
    return regex


@memoize1
def pattern2re(pattern):
    """Makes a unicode regular expression from a pattern.

    Returns ``(start, full_re, int_re)`` where:

     * `start` is either empty or the subdirectory in which to start searching,
     * `full_re` is a regular expression object that matches the requested
       files, i.e. a translation of the pattern
     * `int_re` is either None of a regular expression object that matches
       the requested paths or their ancestors (i.e. if a path doesn't match
       `int_re`, no path under it will match `full_re`)

    This uses extended patterns, where:

      * a slash '/' always represents the path separator
      * a backslash '\' escapes other special characters
      * an initial slash '/' anchors the match at the beginning of the
        (relative) path
      * a trailing '/' suffix is removed
      * an asterisk '*'  matches a sequence of any length (including 0) of any
        characters (except the path separator)
      * a '?' matches exactly one character (except the path separator)
      * '[abc]' matches characters 'a', 'b' or 'c'
      * two asterisks '**' matches one or more path components (might match '/'
        characters)
    """
    pattern_segs = filter(None, pattern.split('/'))

    # This anchors the first component either at the start of the string or at
    # the start of a path component
    if not pattern:
        return '', re.compile(''), None
    elif '/' in pattern:
        full_regex = '^'  # Start at beginning of path
        int_regex = []
        int_regex_done = False
        start_dir = []
        start_dir_done = False
    else:
        full_regex = '(?:^|/)'  # Skip any number of full components
        int_regex = None
        int_regex_done = True
        start_dir = []
        start_dir_done = True

    # Handles each component
    for pnum, pat in enumerate(pattern_segs):
        comp = patterncomp2re(pat)

        # The first component is already anchored
        if pnum > 0:
            full_regex += '/'
        full_regex += comp

        if not int_regex_done:
            if pat == '**':
                int_regex_done = True
            else:
                int_regex.append(comp)
                if not start_dir_done and no_special_chars.match(pat):
                    start_dir.append(pat)
                else:
                    start_dir_done = True

    full_regex = re.compile(full_regex.rstrip('/') + '$')
    if int_regex is not None:
        n = len(int_regex)
        int_regex_s = ''
        for i, c in enumerate(reversed(int_regex)):
            if i == n - 1:  # Last iteration (first component)
                int_regex_s = '^(?:%s%s)?' % (c, int_regex_s)
            elif int_regex_s:
                int_regex_s = '(?:/%s%s)?' % (c, int_regex_s)
            else:  # First iteration (last component)
                int_regex_s = '(?:/%s)?' % c
        int_regex = re.compile(int_regex_s + '$')
    start_dir = '/'.join(start_dir)
    return start_dir, full_regex, int_regex
