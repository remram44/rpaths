#!/bin/sh

set -eux

case "$TEST_MODE"
in
    run_tests|measure_coverage)
        if [ $TRAVIS_PYTHON_VERSION = "2.6" ]; then pip install unittest2; fi
        if [ $TEST_MODE = "measure_coverage" ]; then pip install coveralls; fi
        python setup.py install
        ;;
    check_style)
        pip install flake8
        ;;
esac
