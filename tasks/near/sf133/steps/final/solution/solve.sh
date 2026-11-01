#!/bin/bash
set -e
git -C /work/w01 reset --hard 620c37ef6ffe37b0bdc45c802b7a7287ee59eb91
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
