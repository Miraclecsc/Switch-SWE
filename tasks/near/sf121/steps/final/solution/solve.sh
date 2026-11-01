#!/bin/bash
set -e
git -C /work/w01 reset --hard bb63c53681cd27569ecef99201ba38517d8527b0
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
