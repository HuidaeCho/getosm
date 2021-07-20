#!/usr/bin/env python3
################################################################################
# Project:  GetOSM <https://github.com/HuidaeCho/getosm>
# Authors:  Huidae Cho
# Since:    July 11, 2021
#
# Copyright (C) 2021 Huidae Cho <https://idea.isnew.info/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################################################
"""
This script implements a wxPython demo GUI using GetOSM.
"""

import io
import sys
import wx.lib.statbmp

# https://stackoverflow.com/a/49480246/16079666
if __package__:
    from .getosm import OpenStreetMap
else:
    from getosm import OpenStreetMap


def main():
    zoomer = None
    lat = 0
    lon = 0
    zoom = 0

    def on_mouse(event):
        def zoom(x, y, dz):
            osm.zoom(x, y, dz)

        nonlocal zoomer

        if event.ButtonDown(wx.MOUSE_BTN_LEFT):
            osm.start_dragging(event.x, event.y)
        elif event.Dragging():
            osm.drag(event.x, event.y)
        elif event.WheelDelta > 0:
            if zoomer:
                zoomer.Stop()
            dz = event.WheelRotation / event.WheelDelta * 0.1
            zoomer = wx.CallLater(0, zoom, event.x, event.y, dz)

    app = wx.App()
    root = wx.Frame(None, title="GetOSM wxPython Demo GUI", size=(800, 800))

    map_canvas = wx.lib.statbmp.GenStaticBitmap(root, wx.ID_ANY, wx.NullBitmap,
                                                size=root.Size)
    map_canvas.Bind(wx.EVT_MOUSE_EVENTS, on_mouse)
    map_canvas.Bind(wx.EVT_SIZE, lambda e: osm.resize_map(e.Size.Width,
                                                          e.Size.Height))

    osm = OpenStreetMap(
            wx.Image,
            lambda image: map_canvas.SetBitmap(wx.Bitmap(image)),
            lambda data: wx.Image(io.BytesIO(data)),
            lambda image, tile, x, y: image.Paste(tile, x, y),
            map_canvas.Size.Width, map_canvas.Size.Height,
            lat, lon, zoom)

    root.Show()
    app.MainLoop()


if __name__ == "__main__":
    sys.exit(main())
