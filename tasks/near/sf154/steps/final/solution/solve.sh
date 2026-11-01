#!/bin/bash
set -e
git -C /work/w00 reset --hard 1af2601829eba5feffb3af7fd527473800c2ba6f
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
