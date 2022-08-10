#!/bin/bash -e

PYTHON=python3
if ! hash $PYTHON 2>/dev/null; then
    PYTHON=python
    if ! hash $PYTHON 2>/dev/null; then
        echo No python or python3 interpreter in PATH, aborting
        exit 1
    fi
fi

scriptdir=$(realpath `dirname $0`)
workdir=${WORKSPACE:-$(realpath $scriptdir/..)}

$PYTHON -m venv "$workdir/venv"
