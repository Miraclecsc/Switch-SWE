#!/bin/bash
set -e
git -C /work/w00 reset --hard 60fecd1d445224fa00385f5f1fde75999da7bec8
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
