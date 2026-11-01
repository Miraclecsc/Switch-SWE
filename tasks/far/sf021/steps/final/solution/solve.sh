#!/bin/bash
set -e
git -C /work/w02 reset --hard 7d9d153b66eb3dded684a0cd322f245a12a448a0
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
