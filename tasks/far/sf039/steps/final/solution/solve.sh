#!/bin/bash
set -e
git -C /work/w02 reset --hard a49b94e0fa1b733692e615d5799f6c477bed2cdb
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
