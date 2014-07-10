#!/bin/sh

case "$TEST_MODE"
in
    run_tests)
        coveralls
        ;;
esac
