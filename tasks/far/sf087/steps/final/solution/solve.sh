#!/bin/bash
set -e
git -C /work/w01 reset --hard 888eb1452625196985701e2727c5416b70e969fd
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
