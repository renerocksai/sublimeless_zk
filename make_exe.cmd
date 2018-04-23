@set PATH=%PATH%;C:\Users\rene.schallner\AppData\Local\Continuum\anaconda3\bin
@set PATH=%PATH%;C:\Users\rene.schallner\AppData\Local\Continuum\anaconda3\Scripts

mkdir _deploy

python bundle_version.py --init

cd src

rd dist /S /Q
rd build /S /Q

pyinstaller --windowed --add-data ../themes/monokai.json;themes --add-data ../themes/saved_searches.json;themes --add-data ../themes/saved_searches.json;themes --add-data ../themes/search_results.json;themes --add-data ../themes/solarized_light.json;themes --add-data "../zettelkasten/201804141018 Welcome.md;zettelkasten" --add-data ../zettelkasten/rene_shades.png;zettelkasten --add-data ../saved_searches_default.md;. --add-data ../search_results_default.md;.   sublimeless_zk.py

@REM add --wondowed
@REM add -F above

cd ..

python bundle_version.py --rename-dist

cd src
rd build /S /Q
cd ..