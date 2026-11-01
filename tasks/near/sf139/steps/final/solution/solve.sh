#!/bin/bash
set -e
git -C /work/w01 reset --hard c79d638e27a10fd2359491bbf7ac1effe8a8b3ff
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
