#!/bin/bash
set -e
git -C /work/w00 reset --hard 0614b4fcb0b1230c557a2940fa15d1ab7bee55b0
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
