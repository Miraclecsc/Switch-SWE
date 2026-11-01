#!/bin/bash
set -e
git -C /work/w01 reset --hard 49840e3b82821d0d57e7e20992eb8e1d9af74a7d
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
