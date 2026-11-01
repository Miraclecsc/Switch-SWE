#!/bin/bash
set -e
git -C /work/w01 reset --hard 3a7b67ac269022b0beca06fd8074459db7cf58b4
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
