#!/bin/sh

case "$TEST_MODE"
in
    run_program)
        (while read line; do echo "$line"; sh -c "$line" || exit $?; done)<<'EOF'
        python setup.py install
EOF
        ;;
    check_style)
        pip install flake8
        ;;
esac
