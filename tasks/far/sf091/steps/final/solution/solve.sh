#!/bin/bash
set -e
git -C /work/w01 reset --hard f85021e014a94abe226630bdbc0b66a600fdcefd
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
