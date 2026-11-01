#!/bin/bash
set -e
git -C /work/w02 reset --hard f9abbbbb4898cac96420e5c5b9d34036a94d46bf
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
