#!/bin/bash
set -e
git -C /work/w01 reset --hard 96c90f26622c8f243ad965371eae2c2028a518de
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
