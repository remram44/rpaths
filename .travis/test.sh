#!/bin/sh

run_lines(){
    while read line; do echo "$line"; sh -c "$line" || exit $?; done
}

case "$TEST_MODE"
in
    run_tests)
        run_lines<<'EOF'
        coverage run --source=rpaths.py --branch tests/__main__.py
EOF
        ;;
    check_style)
        run_lines<<'EOF'
        flake8 --ignore=E126 rpaths.py setup.py tests
EOF
        ;;
esac
