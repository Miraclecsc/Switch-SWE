#!/bin/bash
set -e
git -C /work/w01 reset --hard a5b4e55f984ceeff916a3fb386f9119ba5e70b97
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
