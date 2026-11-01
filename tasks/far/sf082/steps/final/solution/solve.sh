#!/bin/bash
set -e
git -C /work/w01 reset --hard 19fbc45b24ca0d577c9b256bb404b0dbaf4903da
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
