#!/bin/bash
set -e
git -C /work/w03 reset --hard 825cd598fdc1d627b67c8c4b36d9f128ac942ec7
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
