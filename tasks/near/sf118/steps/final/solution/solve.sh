#!/bin/bash
set -e
git -C /work/w01 reset --hard af0026cff97a8f28d165d6ac4afb58b2cdc8ffc5
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
