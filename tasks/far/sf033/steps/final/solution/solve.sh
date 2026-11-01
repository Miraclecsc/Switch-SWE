#!/bin/bash
set -e
git -C /work/w00 reset --hard 0c4574a0311108c52302f2aa4738066b21e14377
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
