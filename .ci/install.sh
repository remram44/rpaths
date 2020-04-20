#!/bin/sh

set -eux

case "$TEST_MODE"
in
    run_tests|coverage)
        if [ "2.6" = "$PYTHON_VERSION" ]; then pip install unittest2; fi
        if [ "coverage" = $TEST_MODE ]; then pip install coverage codecov; fi
        python setup.py install
        ;;
    check_style)
        pip install flake8
        ;;
esac
