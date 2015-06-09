#!/bin/sh

set -eux

case "$TEST_MODE"
in
    measure_coverage)
        coveralls
        ;;
esac
