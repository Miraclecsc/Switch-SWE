#!/bin/bash
set -e
git -C /work/w02 reset --hard fc352b2b8ee84071273142375d8babb44333d115
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
