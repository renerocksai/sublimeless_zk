@set PATH=%PATH%;%CONDA_PREFIX%\bin;%CONDA_PREFIX%\Scripts


mkdir _deploy

python bundle_version.py --init

cd src

rd dist /S /Q
rd build /S /Q

REM --windowed
pyinstaller --windowed --add-data ../themes/monokai.json;themes --add-data ../themes/monokai-large-headings.json;themes --add-data ../themes/saved_searches.json;themes --add-data ../themes/search_results.json;themes --add-data ../themes/solarized_light.json;themes --add-data "../zettelkasten/201804141018 Welcome.md;zettelkasten" --add-data ../zettelkasten/rene_shades.png;zettelkasten --add-data ../saved_searches_default.md;. --add-data ../search_results_default.md;.  --add-data ../sublimeless_zk-settings.json;. --add-data ../app_logo_64.png;. --add-data ../app_picture.png;. --add-data ../sublimeless_zk.ico;. --add-binary %CONDA_PREFIX%\Lib\site-packages\pymmd\files\libMultiMarkdown.dll;. --add-binary %CONDA_PREFIX%\Library\bin\libEGL.dll;. --add-binary %CONDA_PREFIX%\Library\bin\libGLESv2.dll;. --add-data ../data/setevi-template.html;data --add-data ../build_commands.json;. -i ../sublimeless_zk.ico sublimeless_zk.py

@REM add -F above

cd ..

python bundle_version.py --rename-dist

cd src
rd build /S /Q
cd ..