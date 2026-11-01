#!/bin/bash
set -e
git -C /work/w04 reset --hard 7f2490132b6bb862483a94f3cb8ee00bef4bf56f
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
