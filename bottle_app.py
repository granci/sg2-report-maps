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
    maps_folder = os.path.join(dir_path, 'country_maps')
    # config_file = os.path.join(dir_path, 'countrydb.json')
    world_map_pv = os.path.join(dir_path, 'pvout_w21cm_borders.png')
    world_map_solar = os.path.join(dir_path, 'pvout_w21cm_latlon+tropics+borders.png')  # TODO: replace by some ghi/dni map!
    world_map_bbox = [-180, 180, 65, -60]
    lat = bottle.request.query.getone("lat", None)
    lon = bottle.request.query.getone("lon", None)
    # whratio = bottle.request.query.getone("whratio", 1)
    map_type = bottle.request.query.getone("type", "cover_map")
    countryCode = bottle.request.query.getone("countryCode", None)
    # west = bottle.request.query.getone('west', None)
    # east = bottle.request.query.getone('east', None)
    # north = bottle.request.query.getone('north', None)
    # south = bottle.request.query.getone('south', None)
    if lat:
        lat = float(lat)
    if lon:
        lon = float(lon)

    try:
        bottle.response.headers['Content-Type'] = "image/png"

        # for grey map (site info):
        if map_type.lower() == "site_location":
            # png = None
            # png = map_generator.generateCountryMap(config_file, countryCode, lat=float(lat), lon=float(lon), whRatio=float(whratio), west=west, east=east, north=north, south=south)
            png = map_generator.generate_site_map(maps_folder, countryCode, lat=lat, lon=lon, circle_radius=10, circle_width=5, circle_fill='blue')

        # for cover_maps:
        else:
            west, east, north, south = world_map_bbox
            if map_type.lower() == "cover_solar":
                world_map = world_map_solar
            else:
                world_map = world_map_pv
            png = map_generator.generate_report_map(world_map, lat=lat, lon=lon, west=west, east=east, north=north, south=south, circle_radiuses=(12, 20), circle_width=3)
        content = png.getvalue()
        png.close()
        return content

    except Exception as e:
        bottle.response.headers['Content-Type'] = "text/plain"
        error_status = "500 - Internal Server Error"
        bottle.response.status = error_status
        # error_response = report_utils.make_error_response(error_status, "Something went wrong, see the error message:", e)
        # return error_response + '\n'
        return "Something went wrong, see the traceback message:\n{}".format(traceback.format_exc())

if __name__ == '__main__':
    bottle.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True, reloader=True)
    # bottle.run(host="http://sg2-reports.herokuapp.com", port=8080, debug=True, reloader=True)
