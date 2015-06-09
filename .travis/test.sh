#!/bin/sh

set -eux

case "$TEST_MODE"
in
    run_tests)
        python tests
        ;;
    check_style)
        flake8 --ignore=E126 rpaths.py setup.py tests
        ;;
    coverage)
        coverage run --source=rpaths.py --branch tests/__main__.py
        ;;
esac
