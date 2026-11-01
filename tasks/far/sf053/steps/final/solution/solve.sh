#!/bin/bash
set -e
git -C /work/w03 reset --hard 6307392c6e590c130e57e991472633c0ceb6af0d
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
