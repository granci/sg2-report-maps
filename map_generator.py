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
import warnings
import json
import StringIO


def generateWorldMap(world_image_path, lat=0, lon=0, west=-180, east=180, north=90, south=-90, circle_radiuses=(9, 15), circle_width=2):
    from PIL import Image, ImageDraw
    if west > 0:
        west -= 360
    if east < 0:
        east += 360
    # circle1_radius = 10
    # circle2_radius = 15
    # circle_width = 2
    with Image.open(world_image_path) as img:
        width, height = img.size
        # print west, east
        # print width, height
        # print lat, lon
        x_point = int(width * (lon - west) / (east - west))
        y_point = int(height * (north - lat) / (north - south))
        # print x_point, y_point
        draw = ImageDraw.Draw(img)
        # draw.ellipse((x_point - circle1_radius, y_point - circle1_radius, x_point + circle1_radius, y_point + circle1_radius), fill=None, outline='black')
        # draw.ellipse((x_point - circle2_radius, y_point - circle2_radius, x_point + circle2_radius, y_point + circle2_radius), fill=None, outline='black')
        # draw.point((x_point, y_point, x_point + circle1_radius, y_point + circle1_radius), fill='black')
        for cr in circle_radiuses:
            for i in range(0, circle_width):
                draw.ellipse((x_point - cr - i, y_point - cr - i, x_point + cr + i, y_point + cr + i), fill=None, outline='black')
                # draw.ellipse((x_point - circle2_radius - i, y_point - circle2_radius - i, x_point + circle2_radius + i, y_point + circle2_radius + i), fill=None, outline='black')
        # print 'elipsa'
        imgdata = StringIO.StringIO()
        # print world_image_path.split('.')[-1]
        img.save(imgdata, format=world_image_path.split('.')[-1])
        # print 'save'
    return imgdata

def generateCountryMap(config_file, countryCode=None, lat=0, lon=0, whRatio=1.2, expandRatio=10, showPlot=False, west=None, east=None, north=None, south=None):
    '''returns png image data (if show=False) of country map, envelope is expanded by ratio'''
    # print 'je tu'
    with warnings.catch_warnings():
        # TODO: do this more effective way:
        warnings.filterwarnings("ignore", category=UserWarning)
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
