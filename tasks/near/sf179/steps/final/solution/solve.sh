#!/bin/bash
set -e
git -C /work/w04 reset --hard 5ef37d364bfb18461da28fd667e4d538ba67255b
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
