#!/bin/bash
set -e
git -C /work/w04 reset --hard 1fe18bd160ee2f9fb3108e2a9d017e16e362c755
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
