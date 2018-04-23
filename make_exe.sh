#!/usr/bin/env bash

VERSION=$(python bundle_version.py --version)
PREFIX=$(python bundle_version.py --prefix)

python bundle_version.py --init
DEPLOY_BASE=$(python bundle_version.py --deploy-dir)

# cx_Freeze approach
DEPLOY_DIR=${DEPLOY_BASE}/semantic_zk-${PREFIX}-${VERSION}-macOS
mkdir -p ${DEPLOY_DIR}

# GUI
rm -fr build/
python build_macos.py bdist_mac 2>&1  |tee build-sublimeless_zk-${PREFIX}-${VERSION}.log
# cp -v Info.plist if_Note_Book_Alt_86976.icns build/sublimeless_zk-${VERSION}.app/Contents/
# cp -v if_Note_Book_Alt_86976.icns build/sublimeless_zk-${VERSION}.app/Contents/icon.icns
mv -v build/sublimeless_zk-${VERSION}.app ${DEPLOY_DIR}/
rm -fr build/
