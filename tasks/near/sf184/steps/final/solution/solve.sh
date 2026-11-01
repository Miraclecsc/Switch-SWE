#!/bin/bash
set -e
git -C /work/w01 reset --hard 4395da09ff8352bb9ced44b9e4fc232cb1ac2fa1
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
