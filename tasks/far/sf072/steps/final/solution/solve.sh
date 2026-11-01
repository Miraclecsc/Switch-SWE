#!/bin/bash
set -e
git -C /work/w02 reset --hard 440797e6196284d8c42e66e0d0e8cc6945d0abc0
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
