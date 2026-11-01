#!/bin/bash
set -e
git -C /work/w01 reset --hard 4580fd6403157037596807bafb2c97b42246e1f3
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
