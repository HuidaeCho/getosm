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
This script implements a tkinter demo GUI using GetOSM.
"""

import sys
import tkinter as tk
from tkinter import ttk
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
    tag_map = "map"
    tag_geoms = "geoms"
    tag_dragged_bbox = "dragged_bbox"
    tag_github = "github"
    github_url = "https://github.com/HuidaeCho/getosm"
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

    lat = 0
    lon = 0
    zoom = 0

    def draw_map(x, y):
        osm.draw()
        draw_geoms(x, y)

    def draw_geoms(x=None, y=None):
        point_size = 4
        point_half_size = point_size // 2
        outline = "blue"
        width = 2
        fill = outline
        stipple = "gray12"

        map_canvas.delete(tag_geoms)

        if curr_geom and x and y:
            latlon = list(osm.canvas_to_latlon(x, y))

            all_geoms = geoms.copy()
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
        else:
            all_geoms = geoms.copy()

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
                        x, y = xy[0]
                        oval = (x - point_half_size, y - point_half_size,
                                x + point_half_size, y + point_half_size)
                        map_canvas.create_oval(oval, outline=outline,
                                               width=width, fill=fill,
                                               tag=tag_geoms)
                elif geom_type == "poly":
                    for xy in osm.get_xy(geom):
                        map_canvas.create_polygon(xy, outline=outline,
                                                  width=width, fill=fill,
                                                  stipple=stipple,
                                                  tag=tag_geoms)
                else:
                    for xy in osm.get_bbox_xy(geom):
                        map_canvas.create_rectangle(xy, outline=outline,
                                                    width=width, fill=fill,
                                                    stipple=stipple,
                                                    tag=tag_geoms)
            g += 1

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

    def zoom_map(x, y, dz, state):
        def zoom(x, y, dz, cancel_event):
            if not cancel_event.wait(0.01) and osm.redownload():
                zoomer_queue.put((draw_map, x, y))

        def check_zoomer():
            nonlocal zoomer

            try:
                draw_map, x, y = zoomer_queue.get_nowait()
            except:
                zoomer.checker = map_canvas.after_idle(check_zoomer)
            else:
                draw_map(x, y)

        nonlocal zoomer

        if state & 0x4:
            # Control + MouseWheel
            if dz > 0:
                geoms_bbox = calc_geoms_bbox()
                if None not in geoms_bbox:
                    osm.zoom_to_bbox(geoms_bbox, False)
            else:
                osm.zoom(x, y, osm.z_min - osm.z, False)
            draw_map(x, y)
            return

        if zoomer:
            zoomer.cancel_event.set()
            osm.cancel = True
            zoomer.join()
            osm.cancel = False
            map_canvas.after_cancel(zoomer.checker)

            cancel_event = zoomer.cancel_event
            cancel_event.clear()
        else:
            cancel_event = threading.Event()

        osm.rescale(x, y, dz)
        zoomer = threading.Thread(target=zoom, args=(x, y, dz, cancel_event))
        zoomer.cancel_event = cancel_event
        zoomer.checker = map_canvas.after_idle(check_zoomer)
        zoomer.start()

    def on_drag(event):
        nonlocal dragged, dragging_bbox, dragged_bbox

        if event.state & 0x4:
            # Control + B1-Motion
            outline = "green"
            width = 2
            fill = outline
            stipple = "gray12"

            latlon = osm.canvas_to_latlon(event.x, event.y)
            if not dragging_bbox:
                dragging_bbox = True
                dragged_bbox.append(latlon)
            else:
                if len(dragged_bbox) == 2:
                    del dragged_bbox[1]
                dragged_bbox.append(latlon)

                ng = len(dragged_bbox)
                s = dragged_bbox[ng-1][0]
                n = dragged_bbox[0][0]
                w = dragged_bbox[0][1]
                e = dragged_bbox[ng-1][1]

                map_canvas.delete(tag_dragged_bbox)
                for xy in osm.get_bbox_xy((s, n, w, e)):
                    map_canvas.create_rectangle(xy, outline=outline,
                                                width=width, fill=fill,
                                                stipple=stipple,
                                                tag=tag_dragged_bbox)
        else:
            osm.drag(event.x, event.y, False)
            draw_map(event.x, event.y)
        dragged = True

    def on_move(event):
        latlon = osm.canvas_to_latlon(event.x, event.y)
        coor_label.config(text=f" {latlon[0]:.4f}, {latlon[1]:.4f} ")
        draw_geoms(event.x, event.y)

    def on_draw(event):
        nonlocal dragged, dragging_bbox, dragged_bbox, drawing_bbox
        nonlocal complete_drawing

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
            map_canvas.delete(tag_dragged_bbox)
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
                # https://stackoverflow.com/a/35855352/16079666
                # don't use .selection_get()
                ranges = geoms_text.tag_ranges(tk.SEL)
                if ranges:
                    index = ranges[0].string
                else:
                    index = geoms_text.index(tk.INSERT)
                line, col = list(map(lambda x: int(x), index.split(".")))
                if col > 0:
                    geoms_string = "\n" + geoms_string
                    line += 1
                if ranges:
                    geoms_text.replace(*ranges, geoms_string)
                else:
                    geoms_text.insert(tk.INSERT, geoms_string)
                geoms_text.mark_set(tk.INSERT, f"{line+1}.0")
                notebook.select(geoms_frame)
                draw_geoms()
        elif not dragged:
            # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-handlers.html
            if event.state & 0x4:
                # Control + ButtonRelease-1
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

        # XXX: sometimes, double-click events occur for both clicks and there
        # is no reliable way to register the first click only using
        # complete_drawing; a hacky way to handle such cases
        if not curr_geom:
            curr_geom.append(osm.canvas_to_latlon(event.x, event.y))
            prev_xy = [event.x, event.y]
        complete_drawing = True

    def on_cancel_drawing(event):
        nonlocal drawing_bbox

        drawing_bbox = False
        curr_geom.clear()
        prev_xy.clear()
        draw_geoms()

    def on_clear_drawing(event):
        geoms_text.delete("1.0", tk.END)
        geoms.clear()

    def ok():
        root.destroy()
        print(geoms)

    #####
    # GUI

    # root window
    root = tk.Tk()
    root_width = 800
    root_height = root_width
    root.geometry(f"{root_width}x{root_height}")
    root.resizable(False, False)
    root.title("GetOSM tkinter Demo GUI")
    # https://stackoverflow.com/a/5871414/16079666
    root.bind_class("Text", "<Control-a>",
                    lambda e: e.widget.tag_add(tk.SEL, "1.0", tk.END))

    ###########
    # top frame
    map_canvas_width = root_width
    map_canvas_height = root_height // 2

    map_canvas = tk.Canvas(root, height=map_canvas_height)
    map_canvas.pack(fill=tk.BOTH)

    osm = OpenStreetMap(
            lambda width, height: map_canvas.delete(tag_map),
            lambda image: map_canvas.tag_lower(tag_map),
            lambda data: tk.PhotoImage(data=data),
            lambda image, tile, x, y:
                map_canvas.create_image(x, y, anchor=tk.NW, image=tile,
                                        tag=tag_map),
            lambda tile, dz: tile.zoom(2**abs(dz)) if dz > 0 else
                             tile.subsample(2**abs(dz)),
            map_canvas_width, map_canvas_height,
            lat, lon, zoom)

    map_canvas.bind("<ButtonPress-1>", lambda e: osm.grab(e.x, e.y))
    map_canvas.bind("<B1-Motion>", on_drag)
    # Linux
    # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-types.html
    map_canvas.bind("<Button-4>", lambda e: zoom_map(e.x, e.y, dzoom, e.state))
    map_canvas.bind("<Button-5>", lambda e: zoom_map(e.x, e.y, -dzoom,
                                                     e.state))
    # Windows and macOS
    # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-types.html
    map_canvas.bind("<MouseWheel>",
                    lambda e: zoom_map(e.x, e.y,
                                       dzoom if e.delta > 0 else -dzoom,
                                       e.state))
    map_canvas.bind("<Motion>", on_move)
    map_canvas.bind("<ButtonRelease-1>", on_draw)
    map_canvas.bind("<Double-Button-1>", on_complete_drawing)
    map_canvas.bind("<ButtonRelease-3>", on_cancel_drawing)
    map_canvas.bind("<Double-Button-3>", on_clear_drawing)

    ##############
    # bottom frame
    notebook_width = root_width
    notebook = ttk.Notebook(root, width=notebook_width)

    geoms_frame = tk.Frame(notebook)
    notebook.add(geoms_frame, text="Geometries")

    help_frame = tk.Frame(notebook)
    notebook.add(help_frame, text="Help")

    notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    #############
    # geoms frame
    geoms_top_frame = tk.Frame(geoms_frame)
    geoms_top_frame.pack(fill=tk.BOTH, expand=True)

    # text for geoms
    geoms_text = tk.Text(geoms_top_frame, width=20, height=1, wrap=tk.NONE)
    geoms_text.bind("<Key>", lambda e: "break" if e.state == 0 else None)
    geoms_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # vertical scroll bar for geoms
    geoms_vscrollbar = tk.Scrollbar(geoms_top_frame)
    geoms_vscrollbar.config(command=geoms_text.yview)
    geoms_vscrollbar.pack(side=tk.LEFT, fill=tk.Y)
    geoms_text.config(yscrollcommand=geoms_vscrollbar.set)

    # horizontal scroll bar for geoms
    geoms_hscrollbar = tk.Scrollbar(geoms_frame, orient=tk.HORIZONTAL)
    geoms_hscrollbar.config(command=geoms_text.xview)
    geoms_hscrollbar.pack(fill=tk.X)
    geoms_text.config(xscrollcommand=geoms_hscrollbar.set)

    geoms_bottom_frame = tk.Frame(geoms_frame)
    geoms_bottom_frame.pack(fill=tk.BOTH)

    # buttons
    tk.Button(geoms_bottom_frame, text="OK", command=ok).pack(
            side=tk.LEFT, expand=True)
    tk.Button(geoms_bottom_frame, text="Cancel", command=root.destroy).pack(
            side=tk.LEFT, expand=True)

    ############
    # help frame

    # text for help
    help_text = tk.Text(help_frame, width=20, height=1, wrap=tk.NONE)
    help_text.insert(tk.END, textwrap.dedent(f"""\
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
            {github_url}"""))
    help_text.tag_add(tag_github, "end - 1 line", "end")
    help_text.tag_config(tag_github, foreground="blue", underline=True)
    help_text.tag_bind(tag_github, "<Enter>",
                       lambda e: help_text.config(cursor="hand2"))
    help_text.tag_bind(tag_github, "<Leave>",
                       lambda e: help_text.config(cursor=""))
    help_text.tag_bind(tag_github, "<Button-1>",
                       lambda e: webbrowser.open(github_url))
    help_text.config(state=tk.DISABLED)
    help_text.pack(fill=tk.BOTH, expand=True)

    # label for coordinates
    coor_label = tk.Label(notebook)
    coor_label.place(relx=1, rely=0, anchor=tk.NE)

    #########
    # run GUI
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main())
