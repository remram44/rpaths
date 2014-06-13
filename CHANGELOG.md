Changelog
=========

0.3 (2014-06-11)
----------------

Bugfixes:
* `Path.read_link()` didn't work at all.
* `AbstractPath.__eq__()` now returns False instead of raising TypeError if the
  objects are not compatible.

Features:
* Adds `AbstractPath.lies_under()`
* `Path.open()` uses `io.open()`. It now accepts the buffering, encoding,
  errors, newline, closefd and opener arguments, and will return unicode
  instead of bytes if opened in text mode (the default) on Python 2.

0.2 (2014-06-09)
----------------

Bugfixes:
* Makes `__hash__` use `normcase` (like `__eq__` does).
* Removes `AbstractPath.relative()` since it only worked for `Path` anyway.
* Fixes `*atime` methods.

Features:
* Adds docstrings everywhere. There is some HTML documentation at ReadTheDocs:
  http://rpaths.remram.fr/

0.1 (2017-06-07)
----------------

* Basic functionality.
* Stores paths as `unicode` or `bytes` depending on path type.
* `AbstractPath`/`Path` separation.
