#!/bin/sh

case "$TEST_MODE"
in
    run_tests)
        (while read line; do echo "$line"; sh -c "$line" || exit $?; done)<<'EOF'
        if [ $TRAVIS_PYTHON_VERSION = "2.6" ]; then pip install unittest2; fi
        python setup.py install
EOF
        ;;
    check_style)
        pip install flake8
        ;;
esac
