#!/bin/bash
set -e
git -C /work/w02 reset --hard 39e29cd3ec2358e6c97b1ea275ba6df3460c0bf1
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
