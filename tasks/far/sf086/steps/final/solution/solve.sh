#!/bin/bash
set -e
git -C /work/w02 reset --hard 8e49113181b7f586a58c48338e3cafc6bb4f495f
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
