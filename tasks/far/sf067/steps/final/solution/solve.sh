#!/bin/bash
set -e
git -C /work/w02 reset --hard 69a2f3f5382aba1ad21aa4e1f8e61b9acfdc642f
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
