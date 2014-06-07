[![Build Status](https://travis-ci.org/remram44/rpaths.svg?branch=master)]
(https://travis-ci.org/remram44/rpaths)

rpaths
===============

rpaths is yet another path manipulation library.

It pains me that I should have to write this, however after a survey of the
existing packages, including [pathlib]
(https://docs.python.org/3/library/pathlib.html) (included in the Python
standard library since 3.4, see [PEP 428]
(http://legacy.python.org/dev/peps/pep-0428/)), it appears that every one of
them chokes on one valid filename or another.

* [Unipath](https://github.com/mikeorr/Unipath) is very close. In fact it is,
with pathlib, one of the main inspirations for this work. Unfortunately it
makes its path inherit from unicode or bytes, which makes the abstract/concrete
class separation too tricky.
* [pathlib](https://docs.python.org/3/library/pathlib.html) is affected with
[a bug preventing it from representing some filenames on Windows on Python 2]
(https://bitbucket.org/pitrou/pathlib/issue/25); this bug was marked as
wontfix. Furthermore, it works very differently on Python 2 and 3, which I
believe is very counter-productive.
* [path.py](https://github.com/jaraco/path.py) is affected with [a bug making
it fail when encountering some filenames on POSIX]
(https://github.com/jaraco/path.py/issues/61). This is also believed to allow
for DoS attacks.
* [fpath](https://github.com/wackywendell/fpath) is affected with the
[same bug](https://github.com/wackywendell/fpath/issues/5) as path.py.