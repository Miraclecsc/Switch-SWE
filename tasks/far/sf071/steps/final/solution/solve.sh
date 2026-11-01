#!/bin/bash
set -e
git -C /work/w01 reset --hard d968ba18927bff786518ea2636cb096792eb4610
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
