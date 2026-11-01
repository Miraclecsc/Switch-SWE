#!/bin/bash
set -e
git -C /work/w03 reset --hard 11a3f1227e69a29fc9dc56f348f982cb5372a1d1
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
