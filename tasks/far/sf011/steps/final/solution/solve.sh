#!/bin/bash
set -e
git -C /work/w00 reset --hard 856c915326768962806705ca7733e4abbb8f794f
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
