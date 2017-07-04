'''
Created on Jan 19, 2010
generates small overview maps for world countries (envelopes stored in database)
maps are generated from basemap module.
Country infos are taken from xml file downloaded from http://ws.geonames.org/countryInfo
use updateCountryDatabase module to update our db.
@author: marek
'''
# from backends.conf import configuration
# import MySQLdb
# import warnings
import json
import StringIO
import os
import math
from PIL import Image, ImageDraw


def generate_report_map(map_image_path, lat=None, lon=None, west=-180., east=180., north=90., south=-90., circle_radiuses=(9, 15), circle_width=2, circle_fill=None):
    # from PIL import Image, ImageDraw
    with Image.open(map_image_path) as img:
        if lat and lon and west and east and north and south:
            if west > 180:
                west -= 360
            if east < -180:
                east += 360
            width, height = img.size
            x_point = int(width * (lon - west) / (east - west))
            y_point = int(height * (north - lat) / (north - south))
            # print lat, lon, west, east, north, south
            # print width, height
            # print x_point, y_point, width * (lon - west) / (east - west), height * (north - lat) / (north - south)
            draw = ImageDraw.Draw(img)
            # draw.ellipse((x_point - circle1_radius, y_point - circle1_radius, x_point + circle1_radius, y_point + circle1_radius), fill=None, outline='black')
            # draw.ellipse((x_point - circle2_radius, y_point - circle2_radius, x_point + circle2_radius, y_point + circle2_radius), fill=None, outline='black')
            # draw.point((x_point, y_point, x_point + circle1_radius, y_point + circle1_radius), fill='black')
            for cr in circle_radiuses:
                for i in range(0, circle_width):
                    # print circle_fill, cr
                    draw.ellipse((x_point - cr - i, y_point - cr - i, x_point + cr + i, y_point + cr + i), fill=circle_fill, outline='black')
                    # draw.ellipse((x_point - circle2_radius - i, y_point - circle2_radius - i, x_point + circle2_radius + i, y_point + circle2_radius + i), fill=None, outline='black')
            # print 'elipsa'
        imgdata = StringIO.StringIO()
        # print world_image_path.split('.')[-1]
        img.save(imgdata, format=map_image_path.split('.')[-1])
        # print 'save'
    return imgdata


def generate_site_map(country_img_dir, country_code=None, lat=None, lon=None, circle_radius=50, circle_width=5, circle_fill='blue'):
    assert os.path.isdir(country_img_dir), "Image folder '{}' does not exist!".format(country_img_dir)
    cntry_images = os.listdir(country_img_dir)
    failover_maps = ["africa", "europe"]
    ultimate_failover = "world"
    # print lat, lon
    # imgdata = None
    img_path = None
    bbox = None

    # try to find proper country map
    for img in cntry_images:
        img_code = img.split("_")[0]
        # if country_code.lower() == img_code.lower():
        if country_code and country_code.lower() == img_code.lower():
            img_path = os.path.join(country_img_dir, img)
            bbox = get_bbox_from_image_name(img_path)
            if lat and lon and bbox and (lat < bbox[1] or lat > bbox[3] or lon < bbox[0] or lon > bbox[2]):  # if doesn't fit to country bbox
                img_path = None

    # failover to continent maps
    lowest_center_distance = 1000  # set something huge
    # if not imgdata:
    if not img_path:
        for img in cntry_images:
            img_code = img.split("_")[0]
            # print img_code, failover_maps
            if img_code in failover_maps:
                failover_img_path = os.path.join(country_img_dir, img)
                failover_bbox = get_bbox_from_image_name(failover_img_path)
                if lat and lon and failover_bbox and lat > failover_bbox[1] and lat < failover_bbox[3] and lon > failover_bbox[0] and lon < failover_bbox[2]:
                    # pythagoras sentence:
                    center_distance = math.sqrt(math.pow((failover_bbox[0] - failover_bbox[2]) / 2 - lon, 2) + math.pow((failover_bbox[1] - failover_bbox[3]) / 2 - lat, 2))
                    # print img_code, center_distance
                    if center_distance < lowest_center_distance:
                        img_path = failover_img_path
                        bbox = failover_bbox

    # failover to world map
    # if not imgdata:
    if not img_path:
        for img in cntry_images:
            img_code = img.split("_")[0]
            if img_code == ultimate_failover:
                img_path = os.path.join(country_img_dir, img)
                bbox = get_bbox_from_image_name(img_path)

    if not bbox:
        bbox = [None, None, None, None]
    imgdata = generate_report_map(img_path, lat=lat, lon=lon, west=bbox[0], east=bbox[2], north=bbox[3], south=bbox[1],
                                  circle_radiuses=(circle_radius,), circle_width=circle_width, circle_fill=circle_fill)

    return imgdata


def get_bbox_from_image_name(image_path):
    """

    :param image_path: string with image path
    :return: list [west, south, east, north] or None (if can not be detected from the file name)
    """
    try:
        bbox = map(float, os.path.splitext(os.path.basename(image_path))[0].split("_")[-1].split(","))
    except:
        bbox = None
    return bbox


def generateCountryMap(config_file, countryCode=None, lat=0, lon=0, whRatio=1.2, expandRatio=10, showPlot=False, west=None, east=None, north=None, south=None):
    '''returns png image data (if show=False) of country map, envelope is expanded by ratio'''
    # print 'je tu'
    # with warnings.catch_warnings():
        # TODO: do this more effective way:
        # warnings.filterwarnings("ignore", category=UserWarning)
    import matplotlib
    if(showPlot==False): matplotlib.use('Agg')
    from pylab import arange,show
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap

    # conf = configuration.getActiveConfig()
    # conn=MySQLdb.connect(host=conf.countryMap_db_host,user=conf.countryMap_db_user,passwd=conf.countryMap_db_password,db=conf.countryMap_db_name)
    # curs = conn.cursor()
    # query="SELECT west,north,east,south FROM countries where code = '"+countryCode+"' ORDER BY name"
    # curs.execute(query)
    # tab=curs.fetchall()
    # conn.close()

    # print config_file
    with open(config_file) as json_file:
        # print json_file.read()
        config_json = json.loads(json_file.read())
        # print 'daco'
        # print config_json
    bbox = None
    for cntry in config_json:
        if countryCode and countryCode.lower() == cntry.get("code", '').lower():
            bbox = [cntry.get("west"), cntry.get("north"), cntry.get("east"), cntry.get("south")]

    failover_extent = lon - 10., lat + 10.,lon + 10.,lat -10.
    location_has_country = True
    if bbox is None:
        # unknown country code, do failover, 10 degree window centered at passed lat lon
        w,n,e,s = failover_extent
        location_has_country = False
    else:
        w,n,e,s = bbox
    w,n,e,s = expandEnvelope(w, n, e, s, expandRatio, whRatio)
    # print w,n,e,s, str(countryCode)

    location_inside_country = False # point belongs to country ISO code, but it's out of the country extent (e.g. distant territories of mainlands)
    if (lon > w and lon < e) and (lat > s and lat < n):
        location_inside_country = True
    if location_inside_country == False and location_has_country:
        w,n,e,s = failover_extent

#	override automatic bounds by user's values
    if west is not None:
        w = float(west)
    if north is not None:
        n = float(north)
    if south is not None:
        s = float(south)
    if east is not None:
        e = float(east)



    #draw png countries
    # fig = plt.figure(figsize=(6,5.7), facecolor='white')
    fig = plt.figure(figsize=(6,5.8), facecolor='white')
    fig.clear()
    fig.add_axes([0.01,0.0,0.9,1.0])
    m0 = Basemap(projection='cyl',llcrnrlon=w,llcrnrlat=s, urcrnrlon=e,urcrnrlat=n, resolution='l')
#		m0 = Basemap(projection='cyl',resolution='i')
    try:
        m0.drawlsmask(land_color='0.9', ocean_color='w', lsmask=None, lsmask_lons=None, lsmask_lats=None, lakes=False)
    except Exception, ex:
        print str(ex.message)
    m0.fillcontinents(color='0.9', lake_color='w')
    m0.drawcoastlines(color='#aaaaaa', linewidth=0.5 )
    m0.drawcountries(color='#777777', linewidth=0.75)
    latRes,lonRes = getLatlonGridRes(w, n, e, s)
    #m0.drawrivers(linewidth=0.3, color='b', antialiased=1)
    m0.drawparallels(arange(-90,90,latRes),linewidth=0.3,dashes=[1,2],labels=[0,1,0,0],xoffset=0.04,size=12, labelstyle=None, fmt='%1.0f')
    m0.drawmeridians(arange(-180,180,lonRes),linewidth=0.3,dashes=[1,2],labels=[0,0,1,0],yoffset=0.01, size=12, labelstyle=None,fmt='%1.0f')
    m0.plot([lon], [lat], 'o', color='red', markersize=9)
    if showPlot:
        show()
        return None
    else:
        # import StringIO
        imgdata = StringIO.StringIO()
        fig.savefig(imgdata, format='png', dpi=100)
        imgdata.seek(0)
        return imgdata

def expandEnvelope(w,n,e,s,percentage, whRatio):
    '''whRatio - w/h ratio, proportion of the image, envelope is adjusted'''
    width = e-w
    height = n-s
    lonExpandRatio = (width * (float(percentage)/100.))/2.
    latExpandRatio = (height * (float(percentage)/100.))/2.
    west = w - lonExpandRatio
    east = e + lonExpandRatio
    north = n + latExpandRatio
    south = s - latExpandRatio
    widthEx = east - west
    heightEx = north - south
    curRatio= widthEx/heightEx
    heightDesired = widthEx / whRatio
    if curRatio > whRatio:
        #expand height (lat) - zvacsit vysku obrazku
        heightDesired = widthEx / whRatio
        latExpandRatio =  (heightDesired - heightEx)/2.
        north = north + latExpandRatio
        south = south - latExpandRatio
    else:
        #expand width (lon) - zvacsit sirku obrazku
        widthDesired = heightEx * whRatio
        lonExpandRatio = (widthDesired - widthEx)/2.
        west = west - lonExpandRatio
        east = east + lonExpandRatio
    #do not expand beyond latlon limits
    if north > 90.:
        north=90.
    if south < -90.:
        south=-90.
    if east > 180.:
        east = 180.
    if west < -180.:
        west = -180.
#	print "w/h ratio=", (east - west)/(north-south)

    return west,north,east,south

def getLatlonGridRes(w,n,e,s, latDensity=3, lonDensity=3):
    '''returns resolution of latlon mesh based on country extent'''
    width = e-w
    height = n-s
    latRes = height/latDensity
    lonRes = width/lonDensity
    latRes=round(latRes,0)
    lonRes = round(lonRes,0)
    if latRes < 1:
        latRes = 1
    if lonRes < 1:
        lonRes = 1
#	print "latRes: ",latRes,"lonRes: ",lonRes
    return latRes,lonRes
