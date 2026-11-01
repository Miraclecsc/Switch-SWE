#!/bin/bash
set -e
git -C /work/w04 reset --hard 3f177d059d65014bf7d1cfd69ffcf5f85807d3f4
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
