#!/bin/bash
set -e
git -C /work/w00 reset --hard 5d9753a3b11228c72e8068f5e5daeeb728c6fc83
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
