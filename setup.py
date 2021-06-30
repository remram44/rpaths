from setuptools import setup


description = """\
rpaths is another path manipulation library. It is heavily inspired by Unipath
and pathlib.

It aims at total Python 2/3 and Windows/POSIX compatibility. To my knowledge,
no other library can handle all the possible paths on every platform.
"""
setup(name='rpaths',
      version='1.0.0',
      py_modules=['rpaths'],
      description='Path manipulation library',
      author="Remi Rampin",
      author_email='remirampin@gmail.com',
      url='https://github.com/remram44/rpaths',
      long_description=description,
      license='BSD',
      keywords=['path', 'file', 'filename', 'pattern', 'fnmatch'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Filesystems'])
