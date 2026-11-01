#!/bin/bash
set -e
git -C /work/w02 reset --hard 97aa0d83da0db0332edc27143669e5eb923c6b17
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
