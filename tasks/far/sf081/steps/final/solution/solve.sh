#!/bin/bash
set -e
git -C /work/w00 reset --hard 46bedf3d307e22901c71e3c03a9f29a0deceb202
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
