#!/bin/bash
set -e
git -C /work/w01 reset --hard ddede2147c9370ab8275f81db4826b6895d2e7dc
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
