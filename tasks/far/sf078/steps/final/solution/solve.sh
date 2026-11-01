#!/bin/bash
set -e
git -C /work/w00 reset --hard 7890ca820eca8580d63fcadae727e95a70daec27
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
