#!/bin/sh
# Clone the two encodings at the commits Paper C uses, into paperC/analysis/_ext/
# (git-ignored). The analysis scripts read the official tests from there.
set -e
cd "$(dirname "$0")"
mkdir -p _ext
cd _ext
[ -d catala-examples ] || git clone -q https://github.com/CatalaLang/catala-examples.git
git -C catala-examples checkout -q 2694b17ddd7c2246e207e8f077d586349ee5abea
[ -d openfisca-aotearoa ] || git clone -q https://github.com/digitalaotearoa/openfisca-aotearoa.git
git -C openfisca-aotearoa checkout -q 9d77ea7ce3c45b6292d4b4eaf3566b2fb00e7ceb
echo "catala-examples    $(git -C catala-examples rev-parse HEAD)"
echo "openfisca-aotearoa $(git -C openfisca-aotearoa rev-parse HEAD)"
