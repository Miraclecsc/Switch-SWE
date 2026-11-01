#!/bin/bash
set -e
git -C /work/w00 reset --hard dba3f2a283a14dacb033777b9a9b2a0540b1b949
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
