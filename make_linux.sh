#!/usr/bin/env bash

mkdir _deploy

python bundle_version.py --init

cd src

rm -fr dist
rm -fr build


pyinstaller  --windowed --add-data ../themes/monokai.json:themes ../themes/monokai-large-headings.json:themes --add-data ../themes/saved_searches.json:themes --add-data ../themes/search_results.json:themes --add-data ../themes/solarized_light.json:themes --add-data "../zettelkasten/201804141018 Welcome.md:zettelkasten" --add-data ../zettelkasten/rene_shades.png:zettelkasten --add-data ../saved_searches_default.md:. --add-data ../search_results_default.md:.  --add-data ../sublimeless_zk-settings.json:. --add-data ../app_logo_64.png:. --add-data ../app_picture.png:. --add-data ../sublimeless_zk.ico:. --add-binary ~/anaconda3/lib/python3.6/site-packages/pymmd/files/libMultiMarkdown.dylib:. --add-binary ~/anaconda3/lib/python3.6/site-packages/pymmd/files/libMultiMarkdown.so:. --add-data ../data/setevi-template.html:data --add-data ../build_commands.json:. -i ../sublimeless_zk.ico sublimeless_zk.py


cd ..

python bundle_version.py --rename-dist

# for chrome when opening browser
final_dir=$(python bundle_version.py --dist-dir)
cp -v /usr/lib/x86_64-linux-gnu/nss/* $final_dir/

cd src
rm -fr build dist
cd ..
