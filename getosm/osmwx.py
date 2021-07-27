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
import threading
import queue

# https://stackoverflow.com/a/49480246/16079666
if __package__:
    from .getosm import OpenStreetMap
else:
    from getosm import OpenStreetMap


def main():
    zoomer = None
    zoomer_queue = queue.Queue()
    dzoom = 0.1

    lat = 0
    lon = 0
    zoom = 0

    def on_mouse(event):
        def zoom(x, y, dz, cancel_event):
            if not cancel_event.wait(0.01) and osm.redownload():
                zoomer_queue.put(osm.draw)

        def check_zoomer():
            nonlocal zoomer

            try:
                draw_map = zoomer_queue.get_nowait()
            except:
                zoomer.checker = wx.CallLater(0, check_zoomer)
            else:
                draw_map()

        nonlocal zoomer

        if event.ButtonDown(wx.MOUSE_BTN_LEFT):
            osm.grab(event.x, event.y)
        elif event.Dragging():
            osm.drag(event.x, event.y)
        elif event.WheelDelta > 0:
            if zoomer:
                zoomer.cancel_event.set()
                osm.cancel = True
                zoomer.join()
                osm.cancel = False
                zoomer.checker.Stop()

                cancel_event = zoomer.cancel_event
                cancel_event.clear()
            else:
                cancel_event = threading.Event()

            dz = event.WheelRotation / event.WheelDelta * dzoom

            # if used without osm.draw(), it works; otherwise, only osm.draw()
            # is visible; timing?
            osm.rescale(event.x, event.y, dz)
            zoomer = threading.Thread(target=zoom, args=(event.x, event.y, dz,
                                                         cancel_event))
            zoomer.cancel_event = cancel_event
            zoomer.checker = wx.CallLater(0, check_zoomer)
            zoomer.start()

    #####
    # GUI

    # root window
    app = wx.App()
    root_width = 800
    root_height = root_width
    root_size = (root_width, root_height)
    root = wx.Frame(None, title="GetOSM wxPython Demo GUI", size=root_size)

    map_canvas = wx.lib.statbmp.GenStaticBitmap(root, wx.ID_ANY, wx.NullBitmap,
                                                size=root.Size)
    map_canvas.Bind(wx.EVT_MOUSE_EVENTS, on_mouse)
    map_canvas.Bind(wx.EVT_SIZE, lambda e: osm.resize(e.Size.Width,
                                                          e.Size.Height))

    osm = OpenStreetMap(
            wx.Image,
            lambda image: map_canvas.SetBitmap(wx.Bitmap(image)),
            lambda data: wx.Image(io.BytesIO(data)),
            lambda image, tile, x, y: image.Paste(tile, x, y),
            lambda tile, dz: tile.Scale(tile.Width*2**dz, tile.Height*2**dz),
            map_canvas.Size.Width, map_canvas.Size.Height,
            lat, lon, zoom)

    #########
    # run GUI
    root.Show()
    app.MainLoop()


if __name__ == "__main__":
    sys.exit(main())
