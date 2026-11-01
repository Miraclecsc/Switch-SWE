#!/bin/bash
set -e
git -C /work/w01 reset --hard 15c3d5755df093822b2ed9543d1961aa6f5ec6d9
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
