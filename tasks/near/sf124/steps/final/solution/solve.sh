#!/bin/bash
set -e
git -C /work/w01 reset --hard 3dea5fed077e33c7d8bca4b5eeade5420cb05d27
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
