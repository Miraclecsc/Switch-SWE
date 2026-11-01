#!/bin/bash
set -e
git -C /work/w01 reset --hard b8c30c72043174cce4105ae4a3e4637005a13423
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
