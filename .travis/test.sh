#!/bin/sh

set -eux

export LC_ALL=C

case "$TEST_MODE"
in
    run_tests)
        python tests
        ;;
    check_style)
        flake8 --ignore=E731 rpaths.py setup.py tests
        ;;
    coverage)
        coverage run --source=rpaths.py --branch tests/__main__.py
        ;;
esac
