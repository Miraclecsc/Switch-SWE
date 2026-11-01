#!/bin/bash
set -e
git -C /work/w03 reset --hard b6a31d78523bcb4dc1373756e6421f4fb6212d07
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
