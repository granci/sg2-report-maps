from qgis.core import *
from PyQt4.Qt import QSize, QDomDocument

from general_utils.basic_logger import make_logger

import project
import util

logger = make_logger(__name__)


def fit_map_to_extent(qgis_project_instance, extent=None, composer_name=None, map_item_name=None, fit_map_canvas=True, exact_extent=False,
                      extent_crs_nr=4326):
    assert isinstance(qgis_project_instance, project.QGISProject), "Parameter {} is not an instance of project.QGISProject() object!".format(qgis_project_instance)
    map_crs = qgis_project_instance.map_settings.destinationCrs()
    # if extent:
    if extent_crs_nr is None:
        extent_crs_nr = qgis_project_instance.map_settings.destinationCrs().EpsgCrsId
    logger.debug("Fitting to extent {0} in EPSG{1}...".format(extent, extent_crs_nr))
    assert (isinstance(extent, list) or isinstance(extent, tuple)) and len(extent) == 4, "Extent must be iterable of 4 numbers!"
    extent_crs = QgsCoordinateReferenceSystem(extent_crs_nr)
    xform = QgsCoordinateTransform(extent_crs, map_crs)
    pt_bl = xform.transform(QgsPoint(extent[0], extent[1]))
    pt_tr = xform.transform(QgsPoint(extent[2], extent[3]))

    extent_rectangle = QgsRectangle(pt_bl, pt_tr)
    logger.debug("New extent in map projection is [{0}] in EPSG{1}!".format(extent_rectangle.asWktCoordinates(), map_crs.srsid()))

    # set map canvas extent:
    if fit_map_canvas:
        if exact_extent:
            qgis_project_instance.canvas.setExtent(extent_rectangle)
        else:
            qgis_project_instance.canvas.zoomToFeatureExtent(extent_rectangle)
        logger.debug("Extent changed in map canvas to {}!".format(extent_rectangle.asWktCoordinates()))

    # set extent in composer(s):
    composition_size = None
    composer_bbox = None
    for c in qgis_project_instance.composers:
        if not composer_name or composer_name == c:
            logger.debug("Processing composer '{}'...".format(c))
            composition = qgis_project_instance.get_composition_object(c)
            # print util.introspect(composition.paperWidth())
            composition_size = composition.paperWidth(), composition.paperHeight()
            for i in range(0, len(composition.composerMapItems())):
                if not map_item_name or composition.composerMapItems()[i].displayName() == map_item_name:
                    composer_map = composition.composerMapItems()[i]
                    if exact_extent:
                        composer_map.setNewExtent(extent_rectangle)
                    else:
                        composer_map.zoomToExtent(extent_rectangle)  # this may work
                    # map_scale = composer_map.scale()
                    # composer_map.requestedExtent(extent_rectangle)
                    # print composer_map.extent().asWktPolygon()
                    # util.introspect(composer_map.extent())
                    # print composer_map.extent().asWktCoordinates()
                    # print composer_map.extent().asWktPolygon()
                    # print composer_map.extent().toRectF()
                    # print composer_map.extent().toString()
                    bbox_wkt = composer_map.extent().asWktCoordinates()
                    sw, ne = bbox_wkt.split(", ")
                    composer_bbox = map(float, sw.split(" ") + ne.split(" "))
                    logger.debug("Extent changed in map '{0}' to {1}!".format(composer_map.displayName(), composer_map.extent().asWktCoordinates()))

    return dict(size=composition_size, bbox=composer_bbox)
    # return qgis_project_instance


def adjust_grid_labels(qgis_project_instance, extent=None, grid_name_part='latlon'):
    # print extent
    # pos_x_string = "1~~1~~if('type'='lat',{east},$x_at(0))~~".format(east=extent[2])
    pos_x_string = "1~~1~~if(&quot;type&quot;='lat',23.250,$x_at(0))~~".format(east=extent[2])

    # pos_y_string = "1~~1~~if('type'='lat',$y_at(0),{north})~~".format(north=extent[3])
    pos_y_string = "1~~1~~if(&quot;type&quot;='lat',$y_at(0),{north})~~".format(north=extent[3])
    # h_ali_string = "1~~1~~'right'~~"
    # v_ali_string = "1~~1~~'half'~~"
    for l in qgis_project_instance.canvas.layers():
        if grid_name_part in l.name():
            # label = l.label()
            # print l.name()
            # util.introspect(label)
            # util.introspect(l)
            # print label.XCoordinate
            # print label.readXML()
            l = modify_layer_customproperty(l, "labeling/dataDefined/PositionX", pos_x_string)
            l = modify_layer_customproperty(l, "labeling/dataDefined/PositionY", pos_y_string)
            # l = modify_layer_customproperty(l, "labeling/dataDefined/Hali", h_ali_string)
            # l = modify_layer_customproperty(l, "labeling/dataDefined/Vali", v_ali_string)
            # break
    return qgis_project_instance


def modify_layer_customproperty(qgis_vector_layer_obj, property_name, value_string):
    XMLDocument = QDomDocument("style")
    XMLMapLayers = XMLDocument.createElement("maplayers")
    XMLMapLayer = XMLDocument.createElement("maplayer")
    qgis_vector_layer_obj.writeLayerXML(XMLMapLayer, XMLDocument)
    if XMLMapLayer.firstChildElement("customproperties").hasChildNodes():
        properties = XMLMapLayer.firstChildElement("customproperties").childNodes()
        for i in range(0, properties.size()):
            property_attr = properties.at(i).attributes().namedItem('key')
            value_attr = properties.at(i).attributes().namedItem('value')
            if property_attr.nodeValue() == property_name:
                value_attr.setNodeValue(value_string)
        XMLMapLayers.appendChild(XMLMapLayer)
        XMLDocument.appendChild(XMLMapLayers)
        logger.debug("Layer's customproperty '{0}' modified to value '{1}'!".format(property_name, value_string))
    else:
        logger.warning("Layer's customproperty '{}' did not get modified!".format(property_name))
    qgis_vector_layer_obj.readLayerXML(XMLMapLayer)
    qgis_vector_layer_obj.reload()
    return qgis_vector_layer_obj


def export_composition_image(qgis_project_instance, output_image_path, output_resolution=None, composer_name=None):
    assert isinstance(qgis_project_instance, project.QGISProject), "Parameter {} is not an instance of project.QGISProject() object!".format(qgis_project_instance)
    for c in qgis_project_instance.composers:
        if not composer_name or composer_name == c:
            logger.debug("Processing composer '{}'...".format(c))
            composition = qgis_project_instance.get_composition_object(c)
            composition.refreshItems()
            if output_resolution:
                image_size = QSize(output_resolution[0], output_resolution[1])
                image = composition.printPageAsRaster(0, image_size)
            else:
                image = composition.printPageAsRaster(0)
            image.save(output_image_path)
            logger.debug("Image '{}' created!".format(output_image_path))
