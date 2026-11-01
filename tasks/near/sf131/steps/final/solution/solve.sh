#!/bin/bash
set -e
git -C /work/w02 reset --hard 014f0e2efaca4e34a0f4b4b1a28a70296035e09d
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
