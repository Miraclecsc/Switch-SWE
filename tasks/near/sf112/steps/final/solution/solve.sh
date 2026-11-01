#!/bin/bash
set -e
git -C /work/w04 reset --hard 448fe0e6ef233679f34f22e3de0ec6bb446ebb3c
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
