#!/bin/bash
set -e
git -C /work/w01 reset --hard c4844254e6db0cb804c240ba07405db73d810e0b
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
