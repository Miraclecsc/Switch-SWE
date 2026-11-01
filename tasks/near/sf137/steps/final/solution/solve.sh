#!/bin/bash
set -e
git -C /work/w04 reset --hard 5b9630f50fde938b72ad8c99542efe3a6f5717e2
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
