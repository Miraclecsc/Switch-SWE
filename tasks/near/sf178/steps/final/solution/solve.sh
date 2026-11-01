#!/bin/bash
set -e
git -C /work/w00 reset --hard 7a13c041dbef42f9f3feb14110f02626f6892e9a
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
