# ![Patchance Logo](https://raw.githubusercontent.com/Houston4444/Patchance/master/resources/main_icon/128x128/patchance.png) Patchance

Patchance is one more JACK patchbay GUI for GNU/Linux systems, but it could be adapted to Mac and Windows with little effort.
It is a direct alternative to [Catia](https://github.com/falkTX/Catia) or [Patchage](https://github.com/drobilla/patchage).

![Screenshot](https://raw.githubusercontent.com/Houston4444/Patchance/master/screenshots/yellow_boards.png)

## Features:
* Stereo detection for port grouping with their name, for faster connections and readability
* Wrap/Unwrap boxes to can hide things you don't need
* Prevent the boxes from overlapping
* Search a box with a pattern
* Connection with double click for easier touchpad use
* Connection from context menu
* Editable themes (9 Themes embedded)
* show only Audio, only MIDI, or only CV ports
* Transport controls
* Customizable tool bar
* many others...

As [RaySession](https://github.com/Houston4444/RaySession), it is based on the [HoustonPatchbay](https://github.com/Houston4444/HoustonPatchbay) submodule which provides portgroups, wrappable boxes, editable themes and many other nice features.

__RaySession__ users won't find any interest to use __Patchance__, __Patchance__ is for theses ones who think they don't need this session manager.

It is a simple app for __HoustonPatchbay__ and it shows the possibility for any python Qt app to implement this submodule easily.

## Goals

No mystery, the main goal of this software is too show to other devs the possibility to embbed the [HoustonPatchbay](https://github.com/Houston4444/HoustonPatchbay) submodule. Then, if someone has the motivation to implement new features, it is really welcome, I still have [many ideas](https://github.com/Houston4444/HoustonPatchbay/blob/main/plans.md).

Users can easily and quickly write patchbay themes, there are surely others who are better at creating beautiful things than I am.

I think this is also a good approach for first-time users, before they realise that using a session manager makes life easier.

## History

__Patchance__ is not directly a __Catia__ fork, but it comes from.
Originally, the _patchanvas_ module (present in HousPatchbay submodule) has been copied from __Carla__ code. This module was previously copied by @falkTX from __Cadence__ (containing __Catia__ ) to __Carla__.