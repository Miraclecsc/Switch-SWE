#!/bin/bash
set -e
git -C /work/w02 reset --hard 688e33ed050b3c2ebb24473cbb015f3496420bc8
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
