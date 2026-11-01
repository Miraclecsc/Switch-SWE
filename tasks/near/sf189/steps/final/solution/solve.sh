#!/bin/bash
set -e
git -C /work/w01 reset --hard 19943b775d40c018e844f2cb1728442f58112a3b
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
