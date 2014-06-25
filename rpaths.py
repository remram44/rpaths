import contextlib
import fnmatch
import io
import ntpath
import os
import posixpath
import shutil
import sys
import tempfile


__all__ = ["unicode", "Path", "PY3", "PosixPath", "WindowsPath"]

__version__ = '0.4'


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
        self.path = self._lib.normpath(
                self._lib.join(*[self._to_backend(p) for p in parts]))

    def __div__(self, other):
        """Joins two paths.
        """
        return self.__class__(self, other)
    __truediv__ = __div__

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
            return (self._lib.normcase(self.path) == self._lib.normcase(other))

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
            return self._lib.normcase(self.path) < self._lib.normcase(other)

    def __le__(self, other):
        """Compares two paths.

        This will ignore the case on systems where it is not relevant.
        """
        try:
            other = self._to_backend(other)
        except TypeError:
            return NotImplemented
        else:
            return self._lib.normcase(self.path) <= self._lib.normcase(other)

    def __gt__(self, other):
        """Compares two paths.

        This will ignore the case on systems where it is not relevant.
        """
        try:
            other = self._to_backend(other)
        except TypeError:
            return NotImplemented
        else:
            return self._lib.normcase(self.path) > self._lib.normcase(other)

    def __ge__(self, other):
        """Compares two paths.

        This will ignore the case on systems where it is not relevant.
        """
        try:
            other = self._to_backend(other)
        except TypeError:
            return NotImplemented
        else:
            return self._lib.normcase(self.path) >= self._lib.normcase(other)

    def __hash__(self):
        return hash(self._lib.normcase(self.path))

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
            return self.path.decode(self._encoding, 'replace')
        else:
            return self.path

    if PY3:
        __str__ = __unicode__
    else:
        __str__ = __bytes__

    def expand_user(self):
        """Replaces ``~`` or ``~user`` by that `user`'s home directory.
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

        Note that, because all paths are normalized, a root of '.' will be
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
        if root.path != '.':
            components = [root.path]
        else:
            components = []
        if loc.path != self._to_backend('.'):
            components.extend(loc.path.split(self._sep))
        return components

    def ancestor(self, n):
        """Goes up n directories.
        """
        p = self
        for i in range(n):
            p = p.parent
        return p

    def norm_case(self):
        """Removes the case if this flavor of paths is case insensitive.
        """
        return self.__class__(self._lib.normcase(self.path))

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

        for i, (orig_part, dest_part) in enumerate(zip(orig_list, dest_list)):
            if orig_part != self._lib.normcase(dest_part):
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

        If `suffix` is specified, the file name will end with that suffix,
        otherwise there will be no suffix.

        If `prefix` is specified, the file name will begin with that prefix,
        otherwise a default prefix is used.

        If `dir` is specified, the file will be created in that directory,
        otherwise a default directory is used.

        If `text` is specified and true, the file is opened in text mode. Else
        (the default) the file is opened in binary mode.  On some operating
        systems, this makes no difference.

        The file is readable and writable only by the creating user ID.
        If the operating system uses permission bits to indicate whether a
        file is executable, the file is executable by no one. The file
        descriptor is not inherited by children of this process.

        The caller is responsible for deleting the file when done with it.
        """
        if prefix is None:
            prefix = tempfile.template
        fd, filename = tempfile.mkstemp(suffix, prefix, dir, text)
        return fd, cls(filename).absolute()

    @classmethod
    def tempdir(cls, suffix='', prefix=None, dir=None):
        """Returns a new temporary directory.

        Arguments are as for tempfile, except that the `text` argument is
        not accepted.

        The directory is readable, writable, and searchable only by the
        creating user.

        Caller is responsible for deleting the directory when done with it.
        """
        if prefix is None:
            prefix = tempfile.template
        dirname = tempfile.mkdtemp(suffix, prefix, dir)
        return cls(dirname).absolute()

    def absolute(self):
        """Returns a normalized absolutized version of the pathname path.
        """
        return self.__class__(self._lib.abspath(self.path))

    def rel_path_to(self, dest):
        """Builds a relative path leading from this one to another.

        Note that these paths might be both relative, in which case they'll be
        assumed to be considered starting from the same directory.

        Contrary to :class:`~rpaths.AbstractPath`'s version, this will also
        work if one path is relative and the other absolute.
        """
        return self.absolute().rel_path_to(dest.absolute())

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
        """
        files = os.listdir(self.path)
        if pattern is None:
            pass
        elif callable(pattern):
            return filter(pattern, [self / self.__class__(p) for p in files])
        elif isinstance(pattern, backend_types):
            files = fnmatch.filter(files, self._to_backend(pattern))
        else:
            raise TypeError("listdir() expects pattern to be a callable, "
                            "a regular expression or a string pattern, "
                            "got %r" % type(pattern))
        return [self / self.__class__(p) for p in files]

    def recursedir(self, pattern=None, top_down=True):
        """Recursively lists all files under this directory.

        Symbolic links will be walked but files will never be duplicated.
        """
        return self._recursedir(pattern=pattern, top_down=top_down, seen=set())

    def _recursedir(self, pattern, top_down, seen):
        if not self.is_dir():
            raise ValueError("recursedir() called on non-directory %s" % self)
        real_dir = self.resolve()
        if real_dir in seen:
            return
        seen.add(real_dir)
        for child in self.listdir(pattern):
            is_dir = child.is_dir()
            if is_dir and not top_down:
                for grandkid in child._recursedir(pattern, top_down, seen):
                    yield grandkid
            yield child
            if is_dir and top_down:
                for grandkid in child._recursedir(pattern, top_down, seen):
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
        def chown(self, uid, gid):
            """Changes the owner and group id of the path.
            """
            return os.chown(self.path, uid, gid)

    def mkdir(self, name=None, parents=False, mode=0o777):
        """Creates that directory, or a directory under this one.

        ``path.mkdir(name)`` is a shortcut for ``(path/name).mkdir()``.
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

        If parents is True, it will also destroy every empty directory above it
        until an error is encountered.
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

        If `parents` is True, it will create the parent directories of the
        target if they don't exist.
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

        The permissions and times are copied (like copystat).

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
        """
        if name is not None:
            return io.open((self / name).path, mode=mode, **kwargs)
        else:
            return io.open(self.path, mode=mode, **kwargs)
