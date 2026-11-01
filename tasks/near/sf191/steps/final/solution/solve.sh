#!/bin/bash
set -e
git -C /work/w01 reset --hard bfd7bb49b467e7ab586deb475c23974a91df4dab
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
