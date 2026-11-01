#!/bin/bash
set -e
git -C /work/w04 reset --hard 97db7175675a618b78838ccdf4b78108d3eca6f3
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
