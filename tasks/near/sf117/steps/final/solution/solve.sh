#!/bin/bash
set -e
git -C /work/w01 reset --hard ce2ab9ead402a54c68148038101f13ebf2a3636b
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
