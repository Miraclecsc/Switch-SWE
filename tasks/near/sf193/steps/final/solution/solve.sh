#!/bin/bash
set -e
git -C /work/w01 reset --hard 976b8287703d781590d457dffc8b581a244b09d5
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
