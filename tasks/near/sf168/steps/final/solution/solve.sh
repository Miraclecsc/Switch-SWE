#!/bin/bash
set -e
git -C /work/w01 reset --hard 24d3fe74230e5ed49d5ac8b723895493d5aafb0a
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
