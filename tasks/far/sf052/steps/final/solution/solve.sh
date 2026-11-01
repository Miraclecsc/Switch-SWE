#!/bin/bash
set -e
git -C /work/w04 reset --hard 9a464bf68a2e7cc9aed1db8ee50c6aad47fa4fe6
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
