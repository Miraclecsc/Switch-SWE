#!/bin/bash
set -e
git -C /work/w04 reset --hard d40d9f3c97302f3d9bfe7c72e4d5b542e041f3d8
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
