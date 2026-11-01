#!/bin/bash
set -e
git -C /work/w00 reset --hard c1e1167a3e2a9e953fb237656e5609b7bb2a9519
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
