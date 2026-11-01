#!/bin/bash
set -e
git -C /work/w01 reset --hard 58edf3456c3369246e0faa016f360c9e57cba156
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
