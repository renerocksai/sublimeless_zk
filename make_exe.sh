#!/usr/bin/env bash

VERSION=$(python bundle_version.py --version)
PREFIX=$(python bundle_version.py --prefix)

rm -fr _deploy

python bundle_version.py --init
DEPLOY_BASE=$(python bundle_version.py --deploy-dir)

# cx_Freeze approach
mkdir -p ${DEPLOY_BASE}

# GUI
rm -fr build/
python build_macos.py bdist_mac 2>&1  |tee build-sublimeless_zk-${PREFIX}-${VERSION}.log
python bundle_version.py --rename-dist
#rm -fr build/
