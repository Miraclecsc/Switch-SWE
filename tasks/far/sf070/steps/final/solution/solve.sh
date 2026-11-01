#!/bin/bash
set -e
git -C /work/w01 reset --hard aeb4498151f8a99f0e36d5689cd67b9e1137a59b
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
