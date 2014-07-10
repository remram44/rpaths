#!/bin/sh

case "$TEST_MODE"
in
    measure_coverage)
        coveralls
        ;;
esac
