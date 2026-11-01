#!/bin/bash
set -e
git -C /work/w01 reset --hard c2bb296ad5d8d821463d10cf09911dbafff7ca1b
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
