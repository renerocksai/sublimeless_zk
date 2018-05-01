#!/usr/bin/env python3
DEPLOY_DIR = '_deploy'

version = '0.5'
prefix = 'pre'
release_notes = '''
## New features:

*

See the [README](https://github.com/renerocksai/sublimeless_zk) for intstructions.

**Released files:**

* **macOS:** `sublimeless_zk-{prefix}-{version}-macOS.zip`
* **Windows 10:** `sublimeless_zk-{prefix}-{version}-win10.zip`
* **Linux:** `sublimeless_zk-{prefix}-{version}-linux.tar.gz`
'''.format(version=version, prefix=prefix)

# for bash scripts and windows .cmd
if __name__ == '__main__':
    import sys
    import os
    import shutil
    import time

    if len(sys.argv) > 1:
        if sys.argv[1].lower() == '--version':
            print(version)
        elif sys.argv[1].lower() == '--prefix':
            print(prefix)
        elif sys.argv[1].lower() == '--release-notes':
            print(release_notes)
        elif sys.argv[1].lower() == '--tag':
            print('sublimeless_zk-{}-{}'.format(prefix, version))
        elif sys.argv[1].lower() == '--dist-dir':
            release_os = 'linux'
            if sys.platform == 'darwin':
                release_os = 'macOS'
            elif sys.platform == 'win32':
                release_os = 'win10'

            print(os.path.join(DEPLOY_DIR, 'sublimeless_zk-{}-{}-{}'.format(prefix, version, release_os)))
        elif sys.argv[1].lower() == '--init':
            if os.path.exists(DEPLOY_DIR):
                shutil.rmtree(DEPLOY_DIR)
                time.sleep(1)    # bloody windows
            os.makedirs(DEPLOY_DIR)
        elif sys.argv[1].lower() == '--deploy-dir':
            print(DEPLOY_DIR)
        elif sys.argv[1].lower() == '--rename-dist':
            # effing windows is sloooow
            time.sleep(10)
            src = 'dist'
            release_os = 'linux'
            appname = 'sublimeless_zk-{prefix}-{version}'.format(version=version, prefix=prefix)
            if sys.platform == 'win32':
                src = 'src\\dist\\sublimeless_zk'
                release_os = 'win10'
            elif sys.platform == 'darwin':
                appname += '.app'
                src = os.path.join('build', appname)
                release_os = 'macOS'
            else:
                src = os.path.join('src', 'dist', 'sublimeless_zk')
            dest = 'sublimeless_zk-{prefix}-{version}-{os}'.format(version=version, prefix=prefix, os=release_os)
            if sys.platform == 'darwin':
                dest = os.path.join(dest, appname)
            else:
                os.makedirs(dest, exist_ok=True)

            shutil.copytree(src, os.path.join(DEPLOY_DIR, dest))

            zk_dest = os.path.join(DEPLOY_DIR, dest,
                                   'zettelkasten')
            if sys.platform == 'darwin':
                zk_dest = os.path.join(DEPLOY_DIR, dest,
                                       'Contents',
                                       'MacOS',
                                       'zettelkasten')
            for md in os.listdir('zettelkasten'):
                if md.endswith('.md'):
                    shutil.copy2(os.path.join('zettelkasten', md), os.path.join(zk_dest, md))
                    print('Copied', os.path.join('zettelkasten', md), os.path.join(zk_dest, md))
    else:
        print(version, prefix)
