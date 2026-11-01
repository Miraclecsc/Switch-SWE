#!/bin/bash
set -e
git -C /work/w01 reset --hard 0a370316c6a4f0d034da5f90df5a671a32a8e376
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
