#!/bin/bash
set -e
git -C /work/w01 reset --hard c78c9aac17a4d68e0647252310044502f1b7da71
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
