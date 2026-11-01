#!/bin/bash
set -e
git -C /work/w01 reset --hard f02879d8bd86e7634c384d896e356d02611bcb26
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
