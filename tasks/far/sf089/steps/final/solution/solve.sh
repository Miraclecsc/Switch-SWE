#!/bin/bash
set -e
git -C /work/w00 reset --hard ef06fba6df98fa77ebd44546d30696daeeff1d01
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
