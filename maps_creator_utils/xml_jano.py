__author__ = 'jano'
import os
from general_utils import basic_logger
logger =  basic_logger.make_logger(__name__)
from collections import OrderedDict

###### safe python XML stufff ##############################
try:
  from lxml import etree
  logger.debug('running with lxml.etree')
except ImportError:
  try:
    # Python 2.5
    import xml_jano.etree.cElementTree as etree
    logger.debug('running with cElementTree on Python 2.5+')
  except ImportError:
    try:
      # Python 2.5
      import xml_jano.etree.ElementTree as etree
      logger.debug('running with ElementTree on Python 2.5+')
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        logger.debug('running with cElementTree')
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          logger.debug('running with ElementTree')
        except ImportError:
          raise ImportError('Failed to import ElementTree from any known place')

###### python XML stufff ##############################


from lxml import objectify
from json import dumps



def _flatten_attributes(property_name, lookup, attributes):
    if attributes is None:
        return lookup

    if not isinstance(lookup, dict):
        return dict(attributes.items() + [(property_name, lookup)])

    return dict(lookup.items() + attributes.items())


def _xml_element_to_json(xml_element, attributes):
    if isinstance(xml_element, objectify.BoolElement):
        return _flatten_attributes(xml_element.tag, bool(xml_element), attributes)

    if isinstance(xml_element, objectify.IntElement):
        return _flatten_attributes(xml_element.tag, int(xml_element), attributes)

    if isinstance(xml_element, objectify.FloatElement):
        return _flatten_attributes(xml_element.tag, float(xml_element), attributes)

    if isinstance(xml_element, objectify.StringElement):
        return _flatten_attributes(xml_element.tag, str(xml_element).strip(), attributes)

    return _flatten_attributes(xml_element.tag, _xml_to_json(xml_element.getchildren()), attributes)


def _xml_to_json(xml_object):
    attributes = None
    if hasattr(xml_object, "attrib") and not xml_object.attrib == {}:
        attributes = xml_object.attrib

    if isinstance(xml_object, objectify.ObjectifiedElement):
        return _xml_element_to_json(xml_object, attributes)

    if isinstance(xml_object, list):
        if len(xml_object) > 1 and all(xml_object[0].tag == item.tag for item in xml_object):
            return [_xml_to_json(attr) for attr in xml_object]

        return dict([(item.tag, _xml_to_json(item)) for item in xml_object])

    return Exception("Not a valid lxml object")


def xml_to_json(xml):
    xml_object = xml if isinstance(xml, objectify.ObjectifiedElement) \
                     else objectify.fromstring(xml)
    return dumps({xml_object.tag: _xml_to_json(xml_object)})



def extract_element(qgis_project_file=None, element_name=None, as_string=True):
    """
     Extract the element specified by element_name form the QGIS project XML file
    A template would work as well
    :param qgis_project_file: str, fiull path to solarqgis proejct file
    :param element_name:str, the name/tag of the element to be extracted
    :param as_string: bool, if true the element will be returned as a strinb
    :return: str or element object
    """

    tree = etree.parse(qgis_project_file)
    elist = [e_ for e_ in tree.iter() if e_.tag == element_name]

    element =  elist.pop() if elist else None

    if as_string:
        try:
            return etree.tostring(element)
        except TypeError: #None
            return ''
    else:
        return element

def get_components_names(qgis_project_file=None):
    """
    Given a qgis project fetch first level chldren names or the major components

    :param qgis_project_file:
    :return: iterable of str
    """
    tree = etree.parse(qgis_project_file)
    return tuple([e_.tag for e_ in tree.getroot().iterchildren()])

def element2dict(elem, d=None):

    if d is None:
        d = OrderedDict()
    d[elem.tag] = dict(elem.items())
    if len(elem) > 0:
        for c in elem:
            element2dict(c, d=d)
    return d

def elementdict2str(d, s=None, tag=None):
    if s is None:
        s = []
        #tag = d.keys()[0]

    for k, v in d.items():

        if isinstance(v, dict):
            s.append('<%s>' % k)
            elementdict2str(v, s=s, tag=k)

        else:
            s+= ' %s="%s" ' % (k, v)
    if tag:
        s.append('</%s>\n' % tag)

    return ''.join(s)


"""
 if nd is None:
        nd = {}
    for k, v in d.items():
        if issubclass(v.__class__, dict):
            if v:
                validate_cfg_dict(v, nd=nd, section=k)
        else:
            vs = eval(v)
            if vs is not None:

                if section:
                    if not section in nd:
                        nd[section] = {}
                    nd[section][k] = v

                else:
                    nd[k] = v
    return nd
"""

