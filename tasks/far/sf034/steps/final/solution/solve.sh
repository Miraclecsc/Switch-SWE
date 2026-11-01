#!/bin/bash
set -e
git -C /work/w00 reset --hard 841185289d56b5cbdb7fb5b9718c8c97b6339982
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
