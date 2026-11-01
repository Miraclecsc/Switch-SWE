#!/bin/bash
set -e
git -C /work/w01 reset --hard 04172af18099112beca6ec18cdee64c6c1185b1e
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
