#!/bin/bash
set -e
git -C /work/w01 reset --hard 770d4f2254acd5f4c67eaf25634f70ec1640c443
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
