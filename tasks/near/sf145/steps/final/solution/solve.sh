#!/bin/bash
set -e
git -C /work/w01 reset --hard 13ec4c3298e3993b4a87159adece0116dfb603cb
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
