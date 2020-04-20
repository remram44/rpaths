#!/bin/sh

set -eux

case "$TEST_MODE"
in
    run_tests)
        python tests
        ;;
    check_style)
        flake8 --ignore=E731,W504 rpaths.py setup.py tests
        ;;
    coverage)
        coverage run --source=rpaths.py --branch tests/__main__.py
        ;;
esac
