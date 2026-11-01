#!/bin/bash
set -e
git -C /work/w02 reset --hard 18167d99e5cb6eb6c21af1c91333a5122e7a38c4
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
