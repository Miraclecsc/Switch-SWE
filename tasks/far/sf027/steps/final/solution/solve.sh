#!/bin/bash
set -e
git -C /work/w01 reset --hard 50895827ba551a5a8825e7af697bd1a3661de1a3
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
