#!/bin/bash
set -e
git -C /work/w02 reset --hard 15571205e3d2c6327aa5c4294725398ea227e25b
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
