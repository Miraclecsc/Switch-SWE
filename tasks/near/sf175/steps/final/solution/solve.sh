#!/bin/bash
set -e
git -C /work/w03 reset --hard 4fc0e90e1c19faf82bc18f8551eb1ed78dc738ac
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
