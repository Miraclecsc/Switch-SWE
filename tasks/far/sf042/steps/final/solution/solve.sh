#!/bin/bash
set -e
git -C /work/w03 reset --hard 42e3cdf7bd922a5b2d42a8571deede4f234987fc
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
