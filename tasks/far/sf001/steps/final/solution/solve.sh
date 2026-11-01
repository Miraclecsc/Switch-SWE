#!/bin/bash
set -e
git -C /work/w00 reset --hard c40ef2b985fcaccc5fbb23a851e4b5d7f555f68b
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
