#!/bin/bash
set -e
git -C /work/w01 reset --hard 64d7d16d2a30aa31e0ae94b8fffa3673e6ad256c
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
