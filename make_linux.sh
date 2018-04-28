#!/usr/bin/env bash

mkdir _deploy

python bundle_version.py --init

cd src

rm -fr dist
rm -fr build


/home/rene/anaconda3/bin/pyinstaller  --windowed --add-data ../themes/monokai.json:themes --add-data ../themes/saved_searches.json:themes --add-data ../themes/search_results.json:themes --add-data ../themes/solarized_light.json:themes --add-data "../zettelkasten/201804141018 Welcome.md:zettelkasten" --add-data ../zettelkasten/rene_shades.png:zettelkasten --add-data ../saved_searches_default.md:. --add-data ../search_results_default.md:.  --add-data ../sublimeless_zk-settings.json:. --add-data ../app_logo_64.png:. --add-data ../app_picture.png:. --add-data ../sublimeless_zk.ico:. -i ../sublimeless_zk.ico sublimeless_zk.py


cd ..

python bundle_version.py --rename-dist

cd src
rm -fr
cd ..
