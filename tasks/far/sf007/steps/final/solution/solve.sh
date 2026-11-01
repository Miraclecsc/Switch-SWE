#!/bin/bash
set -e
git -C /work/w01 reset --hard 4b2b4bf0ac2707dc9c4d51cabfa72168eaea95fe
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
