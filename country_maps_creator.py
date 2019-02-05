import json
import os
import maps_creator_utils.project
import maps_creator_utils.qgis_utils
from maps_creator_utils import *


if __name__ == '__main__':

    config_filepath = "countrydb.json"
    # gis_filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "maps_creator_utils/grey_map_test.qgs")  # must be specified full path
    gis_filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "maps_creator_utils/greymap/greymap_7x7cm-v3.qgs")  # must be specified full path
    output_folder = "country_maps"
    map_type = "country-map"
    exports_extension = ".png"

    with open(config_filepath) as json_file:
        config_json = json.loads(json_file.read())
    # print config_json
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)
    project_instance = maps_creator_utils.project.QGISProject(qgis_project_file=gis_filepath)
    # project_instance = project.QGISProject(qgis_project_file=gis_filepath)
    for cntry in config_json:
        cntry_code = cntry.get("code", '')
        # if cntry_code == 'europe' or cntry_code == 'africa':
        # bbox = [cntry.get("west"), cntry.get("north"), cntry.get("east"), cntry.get("south")]
        bbox = [cntry.get("west"), cntry.get("south"), cntry.get("east"), cntry.get("north")]
        print "Country code: {0}, bbox: {1}".format(cntry_code, bbox)
        # project_instance = maps_creator_utils.qgis_utils.fit_map_to_extent(project_instance, extent=bbox)
        composer_dict = maps_creator_utils.qgis_utils.fit_map_to_extent(project_instance, extent=bbox, exact_extent=False)
        # print bbox
        # print composer_dict
        # project_instance.save(qgis_project_file="test1.qgs")  # TODO: comment out, for debugging only!
        project_instance = maps_creator_utils.qgis_utils.adjust_grid_labels(project_instance, extent=composer_dict.get('bbox', bbox))
        # print composer_dict.get("bbox")
        # print composer_dict.get("bbox")[0]
        # print round(composer_dict.get("bbox")[0], 5)
        export_filename = cntry_code + "_" + \
                          map_type + "_" + \
                          str(composer_dict.get("size")[0]) + "x" + str(composer_dict.get("size")[1]) + "_" + \
                          str(composer_dict.get("bbox")[0]) + "," + str(composer_dict.get("bbox")[1]) + "," + str(composer_dict.get("bbox")[2]) + "," + str(composer_dict.get("bbox")[3]) + \
                          exports_extension
                          # str(bbox[0]) + "," + str(bbox[1]) + "," + str(bbox[2]) + "," + str(bbox[3]) + \
        print "Image created: {}".format(export_filename)
        export_image_path = os.path.join(output_folder, export_filename)
        # maps_creator_utils.qgis_utils.export_composition_image(exports_project_instance, export_image_path)
        maps_creator_utils.qgis_utils.export_composition_image(project_instance, export_image_path)
        # project_instance.save(qgis_project_file="test2.qgs")  # TODO: comment out, for debugging only!

        # break


