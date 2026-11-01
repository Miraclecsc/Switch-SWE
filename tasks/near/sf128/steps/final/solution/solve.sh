#!/bin/bash
set -e
git -C /work/w00 reset --hard eb1d760fb433d08278816d7ba49477ce86b691a7
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
