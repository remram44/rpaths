Changelog
=========

0.12 (???)
----------

Enhancements:
* Don't follow symlinks in `recursedir()`
* Allow `recursedir()` to keep going by passing it a `handle_errors` callback instead of letting it raise.

Behavior change:
* `recursedir()` now doesn't follow symlinks unless you set `follow_links=True` explicitely

0.11 (2015-08-26)
-----------------

Enhancements:
* Add a `Pattern` class, exposing pattern-matching outside of directory listing.

0.10 (2014-11-06)
-----------------

Bugfixes:
* Fixes a `rel_path_to()` bug on Python 3
* Fixes `'.'.rel_path_to('.')` exception
* Fixes `tempfile()` and `tempdir()` not accepting Path as 'dir' parameter

0.9 (2014-10-20)
----------------

Features:
* unicode() conversion uses `surrogateescape` on Python 3

0.8 (2014-08-15)
----------------

Bugfixes:
* Fixes recursedir()'s recursing on too many folders

Features:
* chown() now has 'no change' defaults for uid and gid
* Adds '+' operator to add a string to the end of the name of a path
* Adds `Path#rewrite()` context-manager, for rewriting a file in-place

0.7 (2014-07-24)
----------------

Features:
* Extended glob filters (à la git, /some/dir*/**/*.log)
* Python 3.2 compatibility

0.6 (2014-07-21)
----------------

Bugfixes:
* Fixes non-working `Path#rel_path_to()`.

0.5 (2014-06-26)
----------------

Features:
* Adds `pattern` parameter to `listdir()` and `recursedir()`

0.4 (2014-06-19)
----------------

Bugfixes:
* Adds missing `__all__` lists
* Actually prevents the creation of `AbstractPath` directly (thanks to VnC-)

Features:
* Adds comparison operators

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

0.1 (2014-06-07)
----------------

* Basic functionality.
* Stores paths as `unicode` or `bytes` depending on path type.
* `AbstractPath`/`Path` separation.
