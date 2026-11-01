#!/bin/bash
set -e
git -C /work/w00 reset --hard ee458799cdb8c95864a0331bd945b4bb11337db9
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
