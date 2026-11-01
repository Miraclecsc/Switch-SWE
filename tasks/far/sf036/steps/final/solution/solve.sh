#!/bin/bash
set -e
git -C /work/w00 reset --hard 37309255b4c1b9c381a2d24a1eaf83100984a16a
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
