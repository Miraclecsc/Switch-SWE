#!/bin/bash
set -e
git -C /work/w04 reset --hard 335c6d0129400eda792f3bec5c71bb28af5e5d37
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
