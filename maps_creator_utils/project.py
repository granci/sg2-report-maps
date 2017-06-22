"""
Improved QGIS python API to facilitate interaction qith QGIS project files, and map layouts

"""
__author__ = 'jano'
import os
from general_utils import basic_logger
logger =  basic_logger.make_logger(__name__)

###### python QGIS stufff ##############################
from qgis.core import *
from qgis.gui import *

from PyQt4.QtCore import QFileInfo, QFile, QTextStream, QIODevice
from PyQt4.Qt import QDomElement, QDomDocument,QDomImplementation

###### python QGIS stufff ##############################


###### local imports ##############################
import xml_jano
import util
from configobj import ConfigObj
from qgis.core import  QgsMapLayerRegistry
###### local imports ##############################


# QGIS_PREFIX_PATH='/usr/share/qgis/'
# QGIS_PREFIX_PATH='/usr/bin/qgis'

# according Milos this must be run just once
app = QgsApplication([], True)
app.initQgis()
# print app.showSettings()
inst = QgsProject.instance()
#layer register singleton..necesary because it caches it's layers and in case 2 project have layers with the same id then it reuses the old layers in a new project
reg = QgsMapLayerRegistry.instance()

class QGISProject(object):
    """
    Wrapper around QgsProject object.
    A QGIS project is just an XML file.
    """

    def __init__(self, qgis_project_file=None):

        # comment up if app doesn't work well
        # self.app = QgsApplication([], True)
        # #this may be necesary on windows
        # #app.setPrefixPath(QGIS_PREFIX_PATH, True)
        # self.app.initQgis()


        util.check_file(qgis_project_file)
        # print 'opening...' + qgis_project_file
        self.tree = xml_jano.etree.parse(qgis_project_file)

        #print self.extract_element(element_name='layer-tree-group')

        self.qprjf = qgis_project_file
        self.doc = QDomDocument()
        self.doc.setContent(xml_jano.etree.tostring(self.tree))
        # print 'opening...'
        f_info = QFileInfo(self.qprjf)
        # print f_info
        self.qprj = inst


        # print self.qprj
        logger.info('Opening QGIS project %s' % self.qprjf)
        self.qprj.setFileName(self.qprjf)
        n_exist_layers = reg.count()

        #layer_tree_el = self.qpath_extract_element(qpath='layer-tree-canvas/custom-order')
        lyrs = self.doc.elementsByTagName('layer-tree-layer')

        #lyrs_dicts = self.doc.elementsByTagName('layer-tree-layer').at(0).toElement().attributeNode('id').name()
        lyr_names =  [lyrs.at(i).toElement().attributeNode('id').value()  for i in range(lyrs.length())]
        if reg.count()> 0:
            reg.removeMapLayers(lyr_names)

        #print util.introspect(layer_tree_el)
        #print self.tree.findall('layer-tree-canvas/custom-order')

        # print 'daco'
        self.qprj.read(f_info)



        self.canvas = QgsMapCanvas()
        # print 'daco'


        #self.canvas_bridge = QgsLayerTreeMapCanvasBridge(self.qprj.layerTreeRoot(), self.canvas)
        self.canvas_bridge = QgsLayerTreeMapCanvasBridge(self.qprj.layerTreeRoot(), self.canvas)

        #clear and add again the layers because soem of them were not added, BUG??
        self.canvas_bridge.clear()
        self.canvas.setLayerSet([QgsMapCanvasLayer(e.layer()) for e in self.qprj.layerTreeRoot().findLayers()])



        # sync canvas bridge in order to keep custom layer order
        self.canvas_bridge.readProject(self.doc)
        self.canvas.readProject(self.doc)

        # default order is probably the one set initially in the project, so this is not needed:
        # if self.canvas_bridge.customLayerOrder():
        #     self.canvas_bridge.setHasCustomLayerOrder(True)

        self.map_settings =  self.canvas.mapSettings()

        #setup compositions
        self.__compositions__ = {}
        for comp_name in self.composers:
            composer_element = self.composer_element(name=comp_name)
            comp_content = xml_jano.etree.tostring(composer_element)
            composer_doc = QDomDocument()
            composer_doc.setContent(comp_content)
            composition = QgsComposition(self.map_settings)
            composition.loadFromTemplate(composer_doc)
            self.__compositions__[comp_name] = composition
            del composer_doc
            del composer_element



    @property
    def components_name(self):
        """
        Return an iterable of string with the tag/name of every child of this project
        :return:
        """
        return xml_jano.get_components_names(self.qprjf)

    def __composer_elements__(self):
        #return xml.extract_element(self.qprjf,element_name='Composer')
        return self.tree.getroot().findall('Composer')

    @property
    def composers(self):
        """
        Returns the name of teh composers stored inside this project
        :return:
        """
        composers = self.__composer_elements__()
        return tuple([c_.get('title') for c_ in composers])

    def composer_element(self, name=None):
        composers = self.__composer_elements__()
        clist = [c_ for c_ in composers if c_.get('title') == name]
        if not clist:
            logger.debug('No composer with name %s was found in %s ' % (name, self.qprjf) )
            return
        else:
            return clist.pop()

    def get_composition_object(self, composer_name=None):
        return self.__compositions__[composer_name]


    def qpath_extract_element(self, qpath=None):
        return self.tree.find(qpath)

    def extract_element(self, element_name=None, as_string=True):
        elist = [e_ for e_ in self.tree.iter() if e_.tag == element_name]

        element = elist.pop() if elist else None

        if as_string:
            try:
                return xml_jano.etree.tostring(element)
            except TypeError:  # None
                return ''
        else:
            return element
    # @property
    # def extent(self):
    #     xmin = float(self.tree.findall('mapcanvas/extent/xmin')[0].text)
    #     ymin = float(self.tree.findall('mapcanvas/extent/ymin')[0].text)
    #     xmax = float(self.tree.findall('mapcanvas/extent/xmax')[0].text)
    #     ymax = float(self.tree.findall('mapcanvas/extent/ymax')[0].text)
    #     return xmin, ymin, xmax, ymax

    def save(self, qgis_project_file=None):
        """

        :param qgis_project_file:
        :return:
        """


        out_file = qgis_project_file or self.qprjf
        logger.info('Saving %s to %s  ' % (self.qprjf, out_file) )
        logger.debug('...creating main "qgis" element')
        #root with attrs
        doc = QDomDocument()
        qgisNode = doc.createElement('qgis')
        qgisNode.setAttribute('projectname', self.qprj.title())
        qgisNode.setAttribute('version', QGis.QGIS_VERSION)
        doc.appendChild(qgisNode)

        #title
        title_node = doc.createElement('title')
        titleText = doc.createTextNode(self.qprj.title())
        title_node.appendChild(titleText)
        qgisNode.appendChild(title_node)
        logger.debug('...creating transaction element')

        #transaction, added in 2.16

        transactionNode = doc.createElement('autotransaction')
        try:
            transactionNode.setAttribute('active', int(self.qprj.autoTransaction()) )
        except AttributeError: # qgis version < 2.16
            transactionNode.setAttribute('active', 0)
        qgisNode.appendChild(transactionNode)

        logger.debug('...creating evaluateDefaultValues element')
        #evaluate defaults
        evaluateDefaultValuesNode = doc.createElement('evaluateDefaultValues')
        try:
            evaluateDefaultValuesNode.setAttribute('active', int(self.qprj.evaluateDefaultValues()))
        except AttributeError:
            evaluateDefaultValuesNode.setAttribute('active', 0)

        qgisNode.appendChild(evaluateDefaultValuesNode)

        #layer tree element
        logger.debug('...creating layer tree element')
        util.introspect(self.canvas, namefilter='legend')
        self.qprj.layerTreeRoot().writeXML(qgisNode)

        #relations,
        logger.debug('...creating relations element')
        relations_el = doc.createElement('relations')
        for rn, r in  self.qprj.relationManager().relations().items():
            r.writeXML(relations_el,doc)
        qgisNode.appendChild(relations_el)
        logger.debug('...creating map canvas/map settings element')
        #now map canvas
        self.canvas.writeProject(doc)

        logger.debug('...creating layer order element for new (>2.4 version) projects ')
        #canvas bridge for layer order in new style (after 2.4 version)
        self.canvas_bridge.writeProject(doc)

        #and it seesm there is old style legend order  (before 2.4 version ) so I add this element as well for compatibility
        if self.canvas_bridge.hasCustomLayerOrder():
            logger.debug('...creating legend element for old style (<2.4 version) projects to specifiy layer order ')
            clorder = self.canvas_bridge.defaultLayerOrder()
            lelem = QgsLayerTreeUtils.writeOldLegend(doc,self.qprj.layerTreeRoot(), self.canvas_bridge.hasCustomLayerOrder(), clorder )
            qgisNode.appendChild(lelem)



        # now the composers
        for composer_name in self.composers:
            logger.debug('...creating composer %s' % composer_name)
            lxml_composer_el = self.qpath_extract_element(qpath='Composer[@title="%s"]' % composer_name)
            title = lxml_composer_el.get('title')
            visible = lxml_composer_el.get('visible')
            qt_composer_doc = QDomDocument()
            qt_composer_doc.setContent('<Composer title="%s" visible="%s"></Composer>' % (title, visible))

            composer_el = qt_composer_doc.documentElement()
            #print qt_composer_doc.toString()
            composition = self.get_composition_object(composer_name=composer_name)

            assert composition.writeXML(composer_el, qt_composer_doc), 'Failed to write composer %s' % composer_name
            qgisNode.appendChild(qt_composer_doc.documentElement())




        #util.introspect(self.qprj.layerTreeRoot(), namefilter='layer')
        projectLayersNode = doc.createElement('projectlayers')
        logger.debug('...creating project layers element')
        for ml in self.canvas.layers():
            maplayerElem = doc.createElement('maplayer')
            ml.writeLayerXML(maplayerElem, doc)
            self.qprj.emit(QtCore.SIGNAL('writeMapLayer'), ml, maplayerElem, doc)
            projectLayersNode.appendChild(maplayerElem)



        qgisNode.appendChild(projectLayersNode)
        #TODO find out how to read all the properties
        logger.debug('...creating project properties')
        prop_content = self.__fetch_properties__()
        prop_doc = QDomDocument()
        prop_doc.setContent(prop_content)

        qgisNode.appendChild(prop_doc.documentElement())



        # util.introspect(self.qprj )
        # print xml.etree.tostring(self.qpath_extract_element('/properties'))
        # print self.qprj.entryList('Digitizing', '')
        # print self.qprj.entryList('/', '')
        # print self.qprj.readEntry('Digitizing', 'SnappingMode')
        # print self.qprj.property('Digitizing')


        self.qprj.visibilityPresetCollection().writeXML(doc)

        # and finally save it
        fh = QFile(out_file)
        qts = QTextStream(fh)
        if not fh.open(QIODevice.WriteOnly):
            raise IOError, unicode(fh.errorString())
        qts.setCodec('UTF-8')
        doc.save(qts, 2)

    def __fetch_properties__(self):
        """
        Save the currect project to a temporary file, and return the settings section as lxml element

        this is because i did not find a nrmal way to fetch the properties form a QgsProject object so i write the prj to disk, read the properties and remove it
        """
        f, fn = os.path.split(self.qprjf)
        temp_prj_n = fn + '.tmp'
        out_file = os.path.join(f, temp_prj_n)
        try:
            outf_info = QFileInfo(out_file)
            self.qprj.write(outf_info), 'failed to save QGIS project to file %s  ' % out_file
            return xml_jano.etree.tostring(xml_jano.etree.parse(self.qprjf).find('/properties'))
        finally:
            os.remove(out_file)

    def _save_(self, qgis_project_file=None):
        out_file = qgis_project_file or self.qprjf
        outf_info = QFileInfo(out_file)
        logger.debug('Saving project to %s' % out_file)

        assert self.qprj.write(outf_info), 'failed to save QGIS project to file %s  ' % out_file

    def __save__(self, qgis_project_file=None):
        """
        Save the currect project. Because the normal project.write
         loses

        :param qgis_project_file: str
        :return: None

        """
        f, fn = os.path.split(self.qprjf)
        temp_prj_n = fn + '.tmp'
        out_filet = os.path.join(f, temp_prj_n)
        out_file = qgis_project_file or self.qprjf
        outf_info = QFileInfo(out_filet)
        if os.path.exists(out_filet):
            os.remove(out_filet)

        logger.debug('Saving project to %s' % out_file)

        assert self.qprj.write(outf_info), 'failed to save QGIS project to file %s  ' % out_filet

        doc = QDomDocument()
        doc.setContent(xml_jano.etree.tostring(xml_jano.etree.parse(out_filet)))

        qgisNode = doc.documentElement()

        os.remove(out_filet)

        # canvas bridge for layer order in new style (after 2.4 version)
        self.canvas_bridge.writeProject(doc)

        # and it seesm there is old style legend order  (before 2.4 version ) so I add this element as well for compatibility
        if self.canvas_bridge.hasCustomLayerOrder():
            logger.debug('...creating legend element for old style (<2.4 version) projects to specifiy layer order ')
            clorder = self.canvas_bridge.customLayerOrder()
            lelem = QgsLayerTreeUtils.writeOldLegend(doc, self.qprj.layerTreeRoot(),
                                                     self.canvas_bridge.hasCustomLayerOrder(), clorder)
            qgisNode.appendChild(lelem)

        # now the composers
        for composer_name in self.composers:
            logger.debug('...creating composer %s' % composer_name)
            lxml_composer_el = self.qpath_extract_element(qpath='Composer[@title="%s"]' % composer_name)
            title = lxml_composer_el.get('title')
            visible = lxml_composer_el.get('visible')
            qt_composer_doc = QDomDocument()
            qt_composer_doc.setContent('<Composer title="%s" visible="%s"></Composer>' % (title, visible))

            composer_el = qt_composer_doc.documentElement()
            # print qt_composer_doc.toString()
            composition = self.get_composition_object(composer_name=composer_name)

            assert composition.writeXML(composer_el, qt_composer_doc), 'Failed to write composer %s' % composer_name
            qgisNode.appendChild(qt_composer_doc.documentElement())

        # and finally save it
        fh = QFile(out_file)
        qts = QTextStream(fh)
        if not fh.open(QIODevice.WriteOnly):
            raise IOError, unicode(fh.errorString())
        qts.setCodec('UTF-8')
        doc.save(qts, 2)


    def composer2pdf(self, composer_name=None, out_pdf_file=None):
        """
        Export the desired composer to pdf specified by out_pdf_file
        :param self:
        :param composer_name:
        :param out_pdf_file:
        :return:
        """
        assert out_pdf_file is not None, 'out_pdf_path in necessary to save the map to pdf'
        assert out_pdf_file != '', 'out_pdf_path can not be empty'
        outfolder, outpdfn = os.path.split(out_pdf_file)
        assert os.path.exists(outfolder), 'The folder where pdf is to be created %s does not exist' % outfolder
        try:
            _f = open(out_pdf_file + '.temp', 'w+')
            os.remove(out_pdf_file + '.temp')
        except Exception:
            raise
        try:
            composition = self.get_composition_object(composer_name=composer_name)
            composition.refreshItems()
            # composition.exportAsPDF(changed_map)
            composition.exportAsPDF(out_pdf_file)

        except Exception as e:
            raise IndexError('Composer %s does not exist in project %s' % (composer_name, self.qprjf))

    def read_cfg_file(self, config_file):
        logger.debug('Parsing %s' % config_file)
        cfg = ConfigObj(config_file, stringify=True, list_values=True, raise_errors=True)
        return cfg

    def merge_configs(self, config_files=None):
        if isinstance(config_files, str):
            config_files = config_files,
        merged_cfg = ConfigObj()
        for cfg_file in config_files:
            cfg = self.read_cfg_file(config_file=cfg_file)
            for section in cfg.sections:
                cfgs = cfg[section]
                try:
                    is_active = cfgs.pop('active' or None)

                    if is_active:

                        id_subsection = [k for k, v in cfgs.items() if 'id' in v ]
                        if id_subsection:
                            print cfgs[id_subsection[0]]['ComposerItem']
                            if not section in merged_cfg:
                                merged_cfg[section] = cfgs
                            else:
                                merged_cfg[section].merge(cfgs)


                        else:
                            raise Exception('Section %s from configuration file %s is invalid because it does not have an "id" key' % (section, cfg_file))
                except KeyError as ke:
                    logger.debug('Section %s from configuration file %s is ignored because it does not have an "active" key' % (section, cfg_file))


        return merged_cfg

    def update_composer(self,composer_name=None, config_files=None):
        """
        Update the composer specified by composer_name using
        settings from multiple configurations files.
        The configuration files must contain sections that have an "active=True" option otherwise are ignored
        Also, all option from sections or subsections are ignored if thei value is None
        They are in the configuration just to show  what are all the properties of a specific composer item

        be aware some options are more tricky to set, for exmple a color qithy jost red value is invalid, you need to set
        all options (alpha, red, green, blue)


        :param composer_name:
        :param config_files:
        :return:
        """


        merged_cfg = self.merge_configs(config_files=config_files)
        # sname is necessary because writeXML can not append to empty QDomDocument
        sname = 'update'

        temp_doc = QDomDocument()
        temp_el = temp_doc.createElement(sname)
        temp_doc.appendChild(temp_el)
        composition = self.get_composition_object(composer_name=composer_name)


        for k, v in merged_cfg.items():
            item_id = v['ComposerItem'].pop('id')
            item = composition.getComposerItemById(item_id)
            item.writeXML(temp_el, temp_doc)
            item_xml_str = temp_doc.toString().replace('<%s>' % sname, '').replace('</%s>' % sname, '').strip()

            lxml_el = xml_jano.etree.fromstring(item_xml_str)

            for e in lxml_el.iter(): #for every element
                if e.tag in v.sections:
                    cfgs = v[e.tag]
                    for an, av in e.items():
                        try:
                            __ = eval(cfgs[an])
                            if __ is not None:
                                raise NameError
                        except KeyError:
                            pass
                        except (NameError, SyntaxError):
                            e.set(an, cfgs[an])
            new_xml_str = xml_jano.etree.tostring(lxml_el)
            tdoc = QDomDocument()
            tdoc.setContent(new_xml_str)
            tel = tdoc.documentElement()
            #update
            item.readXML(tel, tdoc)
            try:
                item.update()
                item.updateItem()
            except AttributeError:
                pass
        composition.refreshItems()








    # def __del__(self):
    #         self.app.exitQgis()





if __name__ == '__main__':
    logger.setLevel('DEBUG')
    logger.debug('Testing QGIS python API')
    qgis_project_file = '/home/jano/Documents/qgis-template/DNI-zambia-v1.qgs'
    nqgis_project_file = '/home/jano/Documents/qgis-template/DNI-zambia-v1_copy.qgs'
    original_map = '/home/jano/Documents/qgis-template/export/original_map.pdf'
    changed_map = '/home/jano/Documents/qgis-template/export/changed_map.pdf'
    p = QGISProject(qgis_project_file=qgis_project_file)
    logger.info('Available Composers: %s' % p.composers)


    if p.composers:
        cname = p.composers[0]
        p.update_composer(composer_name=cname,config_files=('esmap.cfg', 'esmap2.cfg'))
        #
        # logger.debug('Exporting composer %s to PDF' % cname)
        # c =  p.get_composition_object(composer_name=cname)
        # legend_item = c.getComposerItemById('obj_scalebar')
        # legend_item.setAlignment(legend_item.Right)
        # legend_item.update()
        # d  = QDomDocument()
        # el = d.createElement('qgis')
        # legend_item.writeXML(el, d)
        # d.appendChild(el)
        # t = d.toString()
        # print 'id' in t
        # e = xml.etree.fromstring(t)
        # scale_bar = e.getchildren()[0]
        #print xml.etree.tostring(e)
        #config.element2cfg(scale_bar)
        # #util.introspect(legend_item, 'mode')
        # print legend_item.pagePos()



        # c.exportAsPDF(original_map)
        # text = c.getComposerItemById('txt_url')
        # tvalue = text.text()
        # nvalue = 'txt_url'
        # logger.info('Changing "txt_url"\'s map item value from %s to %s' % (tvalue, nvalue))
        # text.setText(nvalue)
        # c.refreshItems()
        # c.exportAsPDF(changed_map)
        #
        p.save(qgis_project_file=nqgis_project_file)
