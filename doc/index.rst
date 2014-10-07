.. _index:

rpaths: a compatible, object-oriented path manipulation library
===============================================================

Introduction
------------

Python provides a module to manipulate filenames: :mod:`os.path`. However, it
is very cumbersome to use (not object-oriented) and difficult to use safely
(because of the bytes/unicode issue).

This library provides classes allowing you to perform all the common operations
on paths easily, using ad-hoc classes.

Moreover, it aims at total Python 2/3 and Windows/POSIX interoperability. In
every case, it will behave the "right way", even when dealing with POSIX
filenames in broken unicode encodings.

Development happens on Github: https://github.com/remram44/rpaths. Feel free to
report bugs, request features or direct your patches there.

Classes
-------

rpaths is organized in two levels. It offers abstract path representations,
which only perform parsing/string manipulation and don't actually perform any
operation on a file system. When dealing with abstract paths, nothing stops you
from manipulating POSIX paths on a Windows host and vice-versa.

On top of these abstract paths comes the concrete :class:`~rpaths.Path` class,
which represents the native type for the current system. It inherits from the
correct abstract class, and adds the actual system operations allowing you to
resolve, list, create or remove files.

Note that, contrary to other path libraries, none of these types inherits from
a built-in string class. However, you can build them from strings in a variety
of ways and :func:`repr`, :func:`bytes` and :func:`unicode` will behave how you
can expect.

Abstract classes
''''''''''''''''

Abstract path behavior is defined by the :class:`~rpaths.AbstractPath` class.
You shouldn't use that directly, use :class:`~rpaths.PosixPath` and
:class:`~rpaths.WindowsPath` which are its implementations.

.. autoclass:: rpaths.AbstractPath
   :members:

.. autoclass:: rpaths.PosixPath

.. autoclass:: rpaths.WindowsPath

Concrete class Path
'''''''''''''''''''

The class Path represents a native path on your system. It inherits from either
:class:`~rpaths.PosixPath` or :class:`~rpaths.WindowsPath`.

.. autoclass:: rpaths.Path
   :members:
