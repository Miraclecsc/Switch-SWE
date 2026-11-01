#!/bin/bash
set -e
git -C /work/w01 reset --hard 8d7a1cacfb3e1a30cbb5d8e207aa1917bad9a3e2
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
