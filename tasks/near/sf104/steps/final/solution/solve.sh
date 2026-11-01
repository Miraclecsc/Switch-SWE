#!/bin/bash
set -e
git -C /work/w02 reset --hard 9f43cccfce3b39b8ac637b4e8cdfe2f0946e9c23
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
