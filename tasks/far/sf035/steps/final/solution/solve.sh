#!/bin/bash
set -e
git -C /work/w00 reset --hard 952f42e958e5887fb297ec4d5607ceec5e1bf20b
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
