#!/bin/bash
set -e
git -C /work/w00 reset --hard 1af2820e3710526248c64d981488f83c3c32e056
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
