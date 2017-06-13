#! /usr/bin/env python
# encoding:UTF-8
import cgi
import map_generator
from backends.conf import configuration
from mod_python import apache


cfg = configuration.getActiveConfig()
sg_version = cfg.solargis_version


def get(req):
    lat = _parse_url_param(req, 'lat', '0')
    lon = _parse_url_param(req, 'lon', '0')
    countryCode = _parse_url_param(req, 'countryCode', '')
    whRatio = _parse_url_param(req, 'whRatio', '1.02')
    west = _parse_url_param(req, 'west', None)
    east = _parse_url_param(req, 'east', None)
    north = _parse_url_param(req, 'north', None)
    south = _parse_url_param(req, 'south', None)

    #	apache.log_error('%s, %s, %s, %s' % (countryCode, lat, lon, whRatio))

    png = map_generator.generateCountryMap(countryCode, float(lat), float(lon), whRatio=float(whRatio), west=west, east=east, north=north, south=south)
    content = png.getvalue()
    req.content_type = "image/png"
    req.set_content_length = len(content)
    req.write(content)
    return apache.OK


def _parse_url_param(requestObj, paramname, default_value):
    param = requestObj.form.getfirst(paramname, default_value)
    if param:
        param = cgi.escape(param)
    return param