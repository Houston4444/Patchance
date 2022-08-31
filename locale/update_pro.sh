#!/bin/bash

# This is a little script for refresh raysession.pro and update .ts files.
# TRANSLATOR: if you want to translate the program, you don't need to run it !

contents=""

this_script=`realpath "$0"`
locale_root=`dirname "$this_script"`
code_root=`dirname "$locale_root"`
cd "$code_root/resources/ui/"

for file in *.ui;do
    contents+="FORMS += ../resources/ui/$file
"
done


cd "$code_root/src/"

for file in *.py;do
    if cat "$file"|grep -q _translate;then
        contents+="SOURCES += ../src/${file}
"
    fi
done


contents+="
TRANSLATIONS += patchance_en.ts
TRANSLATIONS += patchance_fr.ts
"

echo "$contents" > "$locale_root/patchance.pro"

pylupdate5 "$locale_root/patchance.pro"

