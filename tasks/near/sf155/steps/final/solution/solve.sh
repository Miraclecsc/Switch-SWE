#!/bin/bash
set -e
git -C /work/w03 reset --hard 6c70118450b97b6088046d5e71f6a90836ddbc04
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
