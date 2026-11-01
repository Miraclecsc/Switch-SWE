#!/bin/bash
set -e
git -C /work/w00 reset --hard 40a312e80f4f1b25f201293c3f1a840a1b88191d
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
