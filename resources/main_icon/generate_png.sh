#!/bin/bash


sizes="16x16 24x24 32x32 48x48 64x64 96x96 128x128 256x256"
app_name=patchance

for size in $sizes;do
    [ -e $size ] || mkdir $size
    convert -background none -resize $size scalable/$app_name.svg  $size/$app_name.png
done