#!/bin/bash
set -e
git -C /work/w04 reset --hard 44d250a185618d85897253e5ce5ab2ed221904d4
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
