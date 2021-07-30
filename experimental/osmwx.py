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
import textwrap

# https://stackoverflow.com/a/49480246/16079666
if __package__:
    from .getosm import OpenStreetMap
else:
    from getosm import OpenStreetMap


def main():
    github_url = "https://github.com/HuidaeCho/getosm"
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

        if event.Moving():
            latlon = osm.canvas_to_latlon(event.x, event.y)
            coor_label.SetLabel(f"{latlon[0]:.4f}, {latlon[1]:.4f} ")
            main_box.Layout()
        elif event.ButtonDown(wx.MOUSE_BTN_LEFT):
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

    def on_paint(event):
        map_canvas.OnPaint(event)
        dc = wx.PaintDC(map_canvas)


    #####
    # GUI

    # root window
    app = wx.App()
    root_width = 800
    root_height = root_width
    root_size = (root_width, root_height)
    root = wx.Frame(None, title="GetOSM wxPython Demo GUI", size=root_size)
    main_box = wx.BoxSizer(wx.VERTICAL)

    ###########
    # top frame
    map_canvas_width = root_width
    map_canvas_height = root_height // 2
    map_canvas_size = (map_canvas_width, map_canvas_height)

    map_canvas = wx.lib.statbmp.GenStaticBitmap(root, wx.ID_ANY, wx.NullBitmap,
                                                size=map_canvas_size)
    map_canvas.Bind(wx.EVT_MOUSE_EVENTS, on_mouse)
    map_canvas.Bind(wx.EVT_SIZE, lambda e: osm.resize(e.Size.Width,
                                                      e.Size.Height))
    map_canvas.Bind(wx.EVT_PAINT, on_paint)
    main_box.Add(map_canvas)

    osm = OpenStreetMap(
            wx.Image,
            lambda image: map_canvas.SetBitmap(wx.Bitmap(image)),
            lambda data: wx.Image(io.BytesIO(data)),
            lambda image, tile, x, y: image.Paste(tile, x, y),
            lambda tile, dz: tile.Scale(tile.Width*2**dz, tile.Height*2**dz),
            map_canvas.Size.Width, map_canvas.Size.Height,
            lat, lon, zoom)

    #######################
    # label for coordinates
    coor_label = wx.StaticText(root)
    main_box.Add(coor_label, 0, wx.ALIGN_RIGHT)

    ##############
    # bottom frame
    notebook_width = root_width
    notebook_height = root_height - map_canvas_height
    notebook = wx.Notebook(root)

    #############
    # geoms panel
    geoms_panel = wx.Panel(notebook)
    geoms_box = wx.BoxSizer(wx.VERTICAL)

    # text for geoms
    geoms_text = wx.TextCtrl(geoms_panel, style=wx.TE_MULTILINE,
                             size=(notebook_width, notebook_height - 75))
    geoms_box.Add(geoms_text)

    # buttons
    ok_button = wx.Button(geoms_panel, label="OK")
    cancel_button = wx.Button(geoms_panel, label="Cancel")

    geoms_bottom_box = wx.BoxSizer(wx.HORIZONTAL)
    geoms_bottom_box.Add(ok_button, 1)
    geoms_bottom_box.AddStretchSpacer()
    geoms_bottom_box.Add(cancel_button, 1)
    geoms_box.Add(geoms_bottom_box, 0, wx.ALIGN_CENTER)
    geoms_panel.SetSizer(geoms_box)

    notebook.AddPage(geoms_panel, "Geometries")

    ############
    # help panel
    help_panel = wx.Panel(notebook)

    # text for help
    help_text = wx.TextCtrl(help_panel,
                            value=textwrap.dedent(f"""\
            Map operations
            ==============
            Pan:                        Left drag
            Zoom:                       Scroll
            Zoom to geometries:         Ctrl + scroll up
            Zoom to the world:          Ctrl + scroll down
            Draw/zoom to a bbox:        Ctrl + left drag
            Draw a point:               Double left click
            Start drawing a poly:       Left click
            Start drawing a bbox:       Ctrl + left click
            Complete a poly/bbox:       Double left click
            Cancel drawing a poly/bbox: Right click
            Clear geometries:           Double right click

            GitHub repository
            =================
            {github_url}"""),
                            style=wx.TE_MULTILINE | wx.TE_READONLY,
                            size=(notebook_width, notebook_height))
    # https://dzone.com/articles/wxpython-learning-use-fonts
    help_text.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                              wx.FONTWEIGHT_NORMAL))

    help_box = wx.BoxSizer(wx.VERTICAL)
    help_box.Add(help_text)
    help_panel.SetSizer(help_box)

    notebook.AddPage(help_panel, "Help")

    main_box.Add(notebook)

    root.SetSizer(main_box)

    #########
    # run GUI
    root.Show()
    app.MainLoop()


if __name__ == "__main__":
    sys.exit(main())
