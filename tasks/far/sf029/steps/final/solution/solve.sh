#!/bin/bash
set -e
git -C /work/w03 reset --hard 55782a9d802d6e9d4275b1ff1e878c21be10a87c
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
