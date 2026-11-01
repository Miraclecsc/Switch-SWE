#!/bin/bash
set -e
git -C /work/w04 reset --hard 2bc2d36ffc06d41f0c9520c52a2688289d6a02f2
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
