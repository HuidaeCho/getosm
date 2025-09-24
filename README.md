# GetOSM

[![PyPI version](https://badge.fury.io/py/getosm.svg)](https://badge.fury.io/py/getosm)
[![Documentation Status](https://readthedocs.org/projects/getosm/badge/?version=latest)](https://getosm.readthedocs.io/en/latest/?badge=latest)

GetOSM is an OpenStreetMap tile downloader written in Python that is agnostic of
GUI frameworks. It is used with
[tkinter](https://docs.python.org/3/library/tkinter.html) by
[ProjPicker](https://github.com/HuidaeCho/projpicker).

<!-- vim-markdown-toc GFM -->

* [Requirements](#requirements)
* [Installation](#installation)
* [Demo GUIs](#demo-guis)
  * [osmtk: tkinter demo](#osmtk-tkinter-demo)
  * [osmwx: wxPython demo](#osmwx-wxpython-demo)
* [Disclaimer and OpenStreetMap tile usage policy](#disclaimer-and-openstreetmap-tile-usage-policy)
* [License](#license)

<!-- vim-markdown-toc -->

## Requirements

GetOSM uses the following standard Python modules:
* [sys](https://docs.python.org/3/library/sys.html)
* [math](https://docs.python.org/3/library/math.html)
* [urllib.request](https://docs.python.org/3/library/urllib.request.html)

## Installation

```bash
pip install getosm
```

## Demo GUIs

### osmtk: tkinter demo

![image](https://user-images.githubusercontent.com/7456117/126282231-34260f42-316d-4da9-9f0a-b95832f48d85.png)

### osmwx: wxPython demo

![image](https://user-images.githubusercontent.com/7456117/127703838-85809b56-d081-4db1-9184-d3d2673d1c63.png)

## Disclaimer and OpenStreetMap tile usage policy

GetOSM is NOT an official Python package of
[the OpenStreetMap Foundation](https://osmfoundation.org/).

Using this program to bulk-download OpenStreetMap is strictly prohibited by
[their tile usage policy](https://operations.osmfoundation.org/policies/tiles/)
and will get you blocked.

## License

Copyright (C) 2021 [Huidae Cho](https://idea.isnew.info/)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <<https://www.gnu.org/licenses/>>.
