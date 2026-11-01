#!/bin/bash
set -e
git -C /work/w02 reset --hard 8e9a163b44f67502290cfa690c6e42ff43ce3593
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
