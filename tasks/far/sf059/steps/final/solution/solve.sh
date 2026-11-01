#!/bin/bash
set -e
git -C /work/w02 reset --hard d14f005c9649a42019f0d3fd4394d1fd66d54d18
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
