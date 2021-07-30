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
import webbrowser

# https://stackoverflow.com/a/49480246/16079666
if __package__:
    from .getosm import OpenStreetMap
else:
    from getosm import OpenStreetMap


def main():
    github_url = "https://github.com/HuidaeCho/getosm"

    tag_geoms = "geoms"
    tag_dragged_bbox = "dragged_bbox"

    zoomer = None
    zoomer_queue = queue.Queue()
    dzoom = 0.1

    dragged = False
    dragging_bbox = False
    dragged_bbox = []
    drawing_bbox = False
    complete_drawing = False
    prev_xy = []
    curr_geom = []
    geoms = []
    all_geoms = []

    point_size = 4
    line_width = 2
    fill_alpha = 50
    geoms_color = "blue"
    dragged_bbox_color = "green"

    lat = 0
    lon = 0
    zoom = 0

    def draw_map(x, y):
        osm.draw()
        draw_geoms(x, y)

    def draw_geoms(x=None, y=None):
        all_geoms.clear()
        all_geoms.extend(geoms)
        if curr_geom and x and y:
            latlon = list(osm.canvas_to_latlon(x, y))

            g = curr_geom.copy()
            g.append(latlon)

            if drawing_bbox:
                ng = len(g)
                if ng > 0:
                    s = min(g[0][0], g[ng-1][0])
                    n = max(g[0][0], g[ng-1][0])
                    w = g[0][1]
                    e = g[ng-1][1]
                    if s == n:
                        n += 0.0001
                    if w == e:
                        e += 0.0001
                    all_geoms.extend(["bbox", [s, n, w, e]])
            elif g:
                if prev_xy:
                    latlon[1] = adjust_lon(prev_xy[0], x,
                                           curr_geom[len(curr_geom)-1][1],
                                           latlon[1])
                g.append(latlon)
                all_geoms.extend(["poly", g])

        map_canvas.Refresh()

    def adjust_lon(prev_x, x, prev_lon, lon):
        dlon = lon - prev_lon
        if x - prev_x > 0:
            if dlon < 0:
                lon += 360
            elif dlon > 360:
                lon -= 360
        elif dlon > 0:
            lon -= 360
        elif dlon < -360:
            lon += 360
        return lon

    def calc_geoms_bbox():
        s = n = w = e = None
        geom_type = "point"
        g = 0
        ngeoms = len(geoms)
        while g < ngeoms:
            geom = geoms[g]
            if geom in ("point", "poly", "bbox"):
                geom_type = geom
                g += 1
                geom = geoms[g]
            if type(geom) == list:
                if geom_type == "point":
                    lat, lon = geom
                    if s is None:
                        s = n = lat
                        w = e = lon
                    else:
                        if lat < s:
                            s = lat
                        elif lat > n:
                            n = lat
                        if lon < w:
                            w = lon
                        elif lon > e:
                            e = lon
                elif geom_type == "poly":
                    for coor in geom:
                        lat, lon = coor
                        if s is None:
                            s = n = lat
                            w = e = lon
                        else:
                            if lat < s:
                                s = lat
                            elif lat > n:
                                n = lat
                            if lon < w:
                                w = lon
                            elif lon > e:
                                e = lon
                else:
                    b, t, l, r = geom
                    if s is None:
                        s = b
                        n = t
                        w = l
                        e = r
                    else:
                        if b < s:
                            s = b
                        if t > n:
                            n = t
                        if l < w:
                            w = l
                        if r > e:
                            e = r
            g += 1
        if None not in (s, n, w, e):
            if s == n:
                s -= 0.0001
                n += 0.0001
            if w == e:
                w -= 0.0001
                e += 0.0001
        return s, n, w, e

    def on_grab(event):
        osm.grab(event.x, event.y)

    def on_draw(event):
        nonlocal dragged, dragging_bbox, drawing_bbox, complete_drawing

        if dragging_bbox:
            ng = len(dragged_bbox)
            s = min(dragged_bbox[0][0], dragged_bbox[ng-1][0])
            n = max(dragged_bbox[0][0], dragged_bbox[ng-1][0])
            w = dragged_bbox[0][1]
            e = dragged_bbox[ng-1][1]
            if s == n:
                n += 0.0001
            if w == e:
                e += 0.0001
            osm.zoom_to_bbox([s, n, w, e], False)
            dragged_bbox.clear()
            dragging_bbox = False
            draw_map(event.x, event.y)
        elif complete_drawing:
            geoms_string = ""
            geom = []
            if drawing_bbox:
                if len(curr_geom) == 2:
                    s = min(curr_geom[0][0], curr_geom[1][0])
                    n = max(curr_geom[0][0], curr_geom[1][0])
                    w = curr_geom[0][1]
                    e = curr_geom[1][1]
                    geom.extend(["bbox", [s, n, w, e]])
                    geoms_string = f"bbox {s:.4f},{n:.4f},{w:.4f},{e:.4f}"
                drawing_bbox = False
            elif len(curr_geom) == 1:
                lat, lon = curr_geom[0]
                geom.extend(["point", [lat, lon]])
                geoms_string = f"point {lat:.4f},{lon:.4f}"
            elif curr_geom:
                geom.extend(["poly", curr_geom.copy()])
                geoms_string = "poly"
                for g in curr_geom:
                    lat, lon = g
                    geoms_string += f" {lat:.4f},{lon:.4f}"
            geoms.extend(geom)
            curr_geom.clear()
            prev_xy.clear()
            if geoms_string:
                geoms_string += "\n"
                sel = geoms_text.GetSelection()
                if sel[0] > 0 and geoms_text.GetValue()[sel[0] - 1] != "\n":
                    geoms_string = "\n" + geoms_string
                geoms_text.Replace(sel[0], sel[1], geoms_string)
                notebook.ChangeSelection(geoms_panel.page)
                draw_geoms()
        elif not dragged:
            if event.ControlDown():
                drawing_bbox = True
                curr_geom.clear()
            elif drawing_bbox and len(curr_geom) == 2:
                del curr_geom[1]
            latlon = list(osm.canvas_to_latlon(event.x, event.y))
            if not drawing_bbox:
                if prev_xy:
                    latlon[1] = adjust_lon(prev_xy[0], event.x,
                                           curr_geom[len(curr_geom)-1][1],
                                           latlon[1])
                prev_xy.clear()
                prev_xy.extend([event.x, event.y])
            curr_geom.append(latlon)

        dragged = False
        complete_drawing = False

    def on_complete_drawing(event):
        nonlocal complete_drawing

        complete_drawing = True

    def on_cancel_drawing(event):
        nonlocal drawing_bbox

        drawing_bbox = False
        curr_geom.clear()
        prev_xy.clear()
        draw_geoms()

    def on_clear_drawing(event):
        geoms_text.Clear()
        geoms.clear()

    def on_move(event):
        nonlocal dragged, dragging_bbox

        if event.ControlDown() and event.LeftIsDown() and event.Dragging():
            latlon = osm.canvas_to_latlon(event.x, event.y)
            if not dragging_bbox:
                dragging_bbox = True
                dragged_bbox.append(latlon)
            else:
                if len(dragged_bbox) == 2:
                    del dragged_bbox[1]
                dragged_bbox.append(latlon)
                map_canvas.Refresh()
        elif event.LeftIsDown() and event.Dragging():
            osm.drag(event.x, event.y)
            dragged = True
        else:
            latlon = osm.canvas_to_latlon(event.x, event.y)
            coor_label.SetLabel(f"{latlon[0]:.4f}, {latlon[1]:.4f} ")
            main_box.Layout()
            draw_map(event.x, event.y)

    def on_zoom(event):
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

        dz = event.WheelRotation / event.WheelDelta * dzoom

        if event.ControlDown():
            if dz > 0:
                geoms_bbox = calc_geoms_bbox()
                if None not in geoms_bbox:
                    osm.zoom_to_bbox(geoms_bbox, False)
            else:
                osm.zoom(event.x, event.y, osm.z_min - osm.z, False)
            draw_map(event.x, event.y)
            return

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

        # if used without osm.draw(), it works; otherwise, only osm.draw()
        # is visible; timing?
        osm.rescale(event.x, event.y, dz)
        zoomer = threading.Thread(target=zoom, args=(event.x, event.y, dz,
                                                     cancel_event))
        zoomer.cancel_event = cancel_event
        zoomer.checker = wx.CallLater(0, check_zoomer)
        zoomer.start()

    def on_paint(event):
        point_half_size = point_size // 2
        outline = wx.Colour(geoms_color)
        fill = wx.Colour(outline.Red(), outline.Green(), outline.Blue(),
                         fill_alpha)

        map_canvas.OnPaint(event)
        dc = wx.PaintDC(map_canvas)

        dc.SetPen(wx.Pen(outline, width=line_width))

        # not all platforms support alpha?
        # https://wxpython.org/Phoenix/docs/html/wx.Colour.html#wx.Colour.Alpha
        if fill.Alpha() == wx.ALPHA_OPAQUE:
            dc.SetBrush(wx.Brush(fill, wx.BRUSHSTYLE_TRANSPARENT))
        else:
            dc.SetBrush(wx.Brush(fill))

        geom_type = "point"
        g = 0
        ngeoms = len(all_geoms)
        while g < ngeoms:
            geom = all_geoms[g]
            if geom in ("point", "poly", "bbox"):
                geom_type = geom
                g += 1
                geom = all_geoms[g]
            if type(geom) == list:
                if geom_type == "point":
                    for xy in osm.get_xy([geom]):
                        dc.DrawCircle(*xy[0], point_half_size)
                elif geom_type == "poly":
                    for xy in osm.get_xy(geom):
                        dc.DrawPolygon(xy)
                else:
                    for xy in osm.get_bbox_xy(geom):
                        x, y = xy[0]
                        w, h = xy[1][0] - x, xy[1][1] - y
                        dc.DrawRectangle(x, y, w, h)
            g += 1

        if dragged_bbox:
            outline = wx.Colour(dragged_bbox_color)
            fill = wx.Colour(outline.Red(), outline.Green(), outline.Blue(),
                             fill_alpha)

            dc.SetPen(wx.Pen(outline, width=line_width))

            if fill.Alpha() == wx.ALPHA_OPAQUE:
                dc.SetBrush(wx.Brush(fill, wx.BRUSHSTYLE_TRANSPARENT))
            else:
                dc.SetBrush(wx.Brush(fill))

            ng = len(dragged_bbox)
            s = dragged_bbox[ng-1][0]
            n = dragged_bbox[0][0]
            w = dragged_bbox[0][1]
            e = dragged_bbox[ng-1][1]

            for xy in osm.get_bbox_xy((s, n, w, e)):
                x, y = xy[0]
                w, h = xy[1][0] - x, xy[1][1] - y
                dc.DrawRectangle(x, y, w, h)


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
    map_canvas.Bind(wx.EVT_LEFT_DOWN, on_grab)
    map_canvas.Bind(wx.EVT_LEFT_UP, on_draw)
    map_canvas.Bind(wx.EVT_LEFT_DCLICK, on_complete_drawing)
    map_canvas.Bind(wx.EVT_RIGHT_UP, on_cancel_drawing)
    map_canvas.Bind(wx.EVT_RIGHT_DCLICK, on_clear_drawing)
    map_canvas.Bind(wx.EVT_MOTION, on_move)
    map_canvas.Bind(wx.EVT_MOUSEWHEEL, on_zoom)
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
    # https://dzone.com/articles/wxpython-learning-use-fonts
    geoms_text.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                               wx.FONTWEIGHT_NORMAL))
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

    geoms_panel.page = notebook.GetPageCount()
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
                            style=wx.TE_MULTILINE | wx.TE_READONLY |
                                  wx.TE_AUTO_URL,
                            size=(notebook_width, notebook_height))
    help_text.Bind(wx.EVT_TEXT_URL,
                   lambda e: webbrowser.open(github_url)
                             if e.GetMouseEvent().LeftIsDown() else None)
    help_text.SetFont(geoms_text.GetFont())

    help_box = wx.BoxSizer(wx.VERTICAL)
    help_box.Add(help_text)
    help_panel.SetSizer(help_box)

    help_panel.page = notebook.GetPageCount()
    notebook.AddPage(help_panel, "Help")

    main_box.Add(notebook)

    root.SetSizer(main_box)

    #########
    # run GUI
    root.Show()
    app.MainLoop()


if __name__ == "__main__":
    sys.exit(main())
