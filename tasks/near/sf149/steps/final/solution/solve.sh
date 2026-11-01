#!/bin/bash
set -e
git -C /work/w01 reset --hard efa60710fc7dd0d79ac23664c06e33357d59615b
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
