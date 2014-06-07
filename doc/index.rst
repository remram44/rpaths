.. _index:

rpaths: a compatible, object-oriented path manipulation library
===============================================================

Introduction
------------

Python provides a module to manipulate filenames: ``os.path``. However, it is
very cumbersome to use (not object-oriented) and difficult to use safely
(because of the bytes/unicode issue).

This library provides classes allowing you to perform all the common operations
on paths easily, using ad-hoc classes.

Moreover, it aims at total Python 2/3 and Windows/POSIX interoperability. In
every case, it will behave the "right way", even when dealing with POSIX
filenames in broken unicode encodings.

Classes
-------

rpaths is organized in two levels. It offers abstract path representations,
which only perform parsing/string manipulation and don't actually perform any
operation on a file system. When dealing with abstract paths, nothing stops you
from manipulation POSIX paths on a Windows host and vice-versa.

On top of these abstract paths comes the concrete ``Path`` class, which
represents the native type for the current system. It inherits from the correct
abstract class, and adds the actual system operations allowing you to resolve,
list, create or remove files.

Note that, contrary to other path libraries, none of this types inherits from
a built-in string class. However, you can build them from strings in a variety
of ways and repr() or cast them how you'd expect.

Abstract classes
''''''''''''''''

Abstract path behavior is defined by the AbstractPath class. You shouldn't use
that directly, use PosixPath and WindowsPath which are its implementations.

.. autoclass:: rpaths.AbstractPath
   :members:

Concrete class Path
'''''''''''''''''''

The class Path represents a native path on your system. It inherits from either
PosixPath or WindowsPath.

.. autoclass:: rpaths.Path
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
