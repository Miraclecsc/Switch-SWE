#!/bin/bash
set -e
git -C /work/w00 reset --hard ad073338d02fce884301d159f30eaf17c7f2d246
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
