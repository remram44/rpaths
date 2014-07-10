#!/bin/sh

run_lines(){
    while read line; do echo "$line"; sh -c "$line" || exit $?; done
}

case "$TEST_MODE"
in
    run_tests|measure_coverage)
        run_lines<<'EOF'
        if [ $TRAVIS_PYTHON_VERSION = "2.6" ]; then pip install unittest2; fi
        if [ $TEST_MODE = "measure_coverage" ]; then pip install coveralls; fi
        python setup.py install
EOF
        ;;
    check_style)
        pip install flake8
        ;;
esac
