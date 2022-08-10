#!/bin/bash -e

scriptdir=$(realpath `dirname $0`)
workdir=${WORKSPACE:-$(realpath $scriptdir/..)}
pushd "$workdir" > /dev/null

source "$workdir/venv/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

popd > /dev/null
