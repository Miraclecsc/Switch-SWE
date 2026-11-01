#!/bin/bash
set -e
git -C /work/w04 reset --hard 4389d1b701478a1e0a8cc8268fbf5684092c7f49
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
