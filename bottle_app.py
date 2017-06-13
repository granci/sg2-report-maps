#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import traceback
import bottle
import map_generator



app = bottle.default_app()  # bottle WSGI app object

@bottle.get("/")
def get():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.join(dir_path, 'countrydb.json')
    world_map = os.path.join(dir_path, 'pvout_w21cm_borders.png')
    world_map_bbox = [-180, 180, 65, -60]
    lat = bottle.request.query.getone("lat", 0)
    lon = bottle.request.query.getone("lon", 0)
    whratio = bottle.request.query.getone("whratio", 1)
    type = bottle.request.query.getone("type", "site_location")
    countryCode = bottle.request.query.getone("countryCode", None)
    west = bottle.request.query.getone('west', None)
    east = bottle.request.query.getone('east', None)
    north = bottle.request.query.getone('north', None)
    south = bottle.request.query.getone('south', None)

    try:
        bottle.response.headers['Content-Type'] = "image/png"
        if type.lower() == "site_location":
            png = map_generator.generateCountryMap(config_file, countryCode, lat=float(lat), lon=float(lon), whRatio=float(whratio), west=west, east=east, north=north, south=south)
        else:
            west, east, north, south = world_map_bbox
            png = map_generator.generateWorldMap(world_map, lat=float(lat), lon=float(lon), west=west, east=east, north=north, south=south, circle_radiuses=(12, 20), circle_width=3)
        content = png.getvalue()
        # req.content_type = "image/png"
        # req.set_content_length = len(content)
        # req.write(content)
        # return apache.OK
        return content

    except Exception as e:
        error_status = "500 - Internal Server Error"
        bottle.response.status = error_status
        # error_response = report_utils.make_error_response(error_status, "Something went wrong, see the error message:", e)
        # return error_response + '\n'
        return "Something went wrong, see the traceback message:\n{}".format(traceback.format_exc())

if __name__ == '__main__':
    bottle.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True, reloader=True)
    # bottle.run(host="http://sg2-reports.herokuapp.com", port=8080, debug=True, reloader=True)
