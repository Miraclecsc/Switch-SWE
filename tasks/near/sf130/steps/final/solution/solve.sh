#!/bin/bash
set -e
git -C /work/w02 reset --hard 60a9c70496e5d7b971928ce3da5b47c8836a4def
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
