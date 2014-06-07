#!/bin/sh

case "$TEST_MODE"
in
    run_tests)
        (while read line; do echo "$line"; sh -c "$line" || exit $?; done)<<'EOF'
        python tests
EOF
        ;;
    check_style)
        (while read line; do echo "$line"; sh -c "$line" || exit $?; done)<<'EOF'
        flake8 --ignore=E126 rpaths.py setup.py tests
EOF
        ;;
esac
