#!/bin/bash
set -e
git -C /work/w04 reset --hard 9f790ef1a0f356cf6342b5d57bbaeac35aed0d9f
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
