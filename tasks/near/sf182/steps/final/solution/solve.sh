#!/bin/bash
set -e
git -C /work/w04 reset --hard d3f305de93230c44c2923f46b5a18f9a83607509
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
