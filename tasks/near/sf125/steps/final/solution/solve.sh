#!/bin/bash
set -e
git -C /work/w04 reset --hard 787c6888a1827027081cdd10338cf23060b72b94
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
