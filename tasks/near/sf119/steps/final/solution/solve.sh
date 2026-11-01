#!/bin/bash
set -e
git -C /work/w00 reset --hard b20096ccce1ca389fa1d3c4290065ab4ede370cc
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
