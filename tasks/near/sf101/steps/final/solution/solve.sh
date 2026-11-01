#!/bin/bash
set -e
git -C /work/w01 reset --hard 50bbf71bbd51616e2ce48785336ca3746fbe5f24
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
