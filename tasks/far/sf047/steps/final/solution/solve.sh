#!/bin/bash
set -e
git -C /work/w02 reset --hard f99bac28db8630c12b728084d3fb34913be456a7
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
