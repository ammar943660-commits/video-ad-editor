#!/bin/bash
W=$1; shift
for f in "$@"; do ./dev2.sh $W $f 8 ${TAG:-key}; done
