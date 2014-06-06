import contextlib
import os
import shutil
import tempfile


@contextlib.contextmanager
def temp_dir(make=True):
    """Context manager providing a temporary directory.

    make indicates whether the path exist or if the temporary directory can be
    created there.
    """
    path = tempfile.mkdtemp(prefix='test_file_archive_')
    try:
        if make:
            yield path
        else:
            yield os.path.join(path, 'internal')
    finally:
        shutil.rmtree(path)
