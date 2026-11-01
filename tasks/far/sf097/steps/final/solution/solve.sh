#!/bin/bash
set -e
git -C /work/w01 reset --hard 9f8a77d98ebd5bc13b1a111d29b8a22957384e16
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
