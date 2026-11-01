#!/bin/bash
set -e
git -C /work/w03 reset --hard 44ca5eab5499afd567c5cf1f840346326e07de1d
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
