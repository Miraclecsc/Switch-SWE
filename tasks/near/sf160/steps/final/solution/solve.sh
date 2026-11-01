#!/bin/bash
set -e
git -C /work/w00 reset --hard 90538a3b4610ba49ce16c997bcfdb9101f9503be
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
