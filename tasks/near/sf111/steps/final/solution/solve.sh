#!/bin/bash
set -e
git -C /work/w03 reset --hard 6f461522a5c58839c31be3c82b7bd47fba77109b
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
