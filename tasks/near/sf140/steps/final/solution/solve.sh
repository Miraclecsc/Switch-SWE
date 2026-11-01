#!/bin/bash
set -e
git -C /work/w01 reset --hard 825c68f4aef6e9d6e96ef8d5b8baedbde5790ca2
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
