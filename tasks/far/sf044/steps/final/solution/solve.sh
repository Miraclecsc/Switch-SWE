#!/bin/bash
set -e
git -C /work/w02 reset --hard 5d160909eeb42e9844496dd2bbd19b826d2242d7
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
