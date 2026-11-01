#!/bin/bash
set -e
git -C /work/w01 reset --hard 6fad505488504fffd6e8b9bf3ab830fd2b5243ba
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
