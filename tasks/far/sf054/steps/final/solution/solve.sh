#!/bin/bash
set -e
git -C /work/w01 reset --hard 8b648bc213a85613b9441913b82a14d9cd839048
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
