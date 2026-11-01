#!/bin/bash
set -e
git -C /work/w04 reset --hard 9b718ed3d26fc2f80ab58f3249b517a65db9cc7b
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
