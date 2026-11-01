#!/bin/bash
set -e
git -C /work/w01 reset --hard 135ac5b7c1dca4fb8a5da291cc27f560d73b22f9
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
