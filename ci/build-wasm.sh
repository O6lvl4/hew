#!/bin/sh
# Builds hew as a WebAssembly component that starts no process: build/hew.wasm.
#
#   ci/build-wasm.sh
#
# The source is copied, wasm/helper.almd is put in place of src/helper.almd (the one file
# that starts a program, for an outline provider), and the copy is built for the wasm
# target. Under a host that grants a directory read-only and nothing else, the component
# can outline, show and search what is in that directory, and can do nothing more.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp -R "$here/src" "$here/almide.toml" "$here/almide.lock" "$work/"
cp "$here/wasm/helper.almd" "$work/src/helper.almd"
mkdir -p "$here/build"
( cd "$work" && "${ALMIDE:-almide}" build src/main.almd --target wasm -o "$here/build/hew.wasm" )
