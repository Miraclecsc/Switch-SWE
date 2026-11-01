#!/bin/bash
set -e
git -C /work/w01 reset --hard a7247a70534d34769b04d8de83b5f94772d111f9
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
