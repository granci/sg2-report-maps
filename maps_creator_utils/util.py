"""
utility functions for qgis module
"""

import os
def check_file(file_path=None):
    """
    makes sure the input file is real, exists, is absolute, etc
    Perhaps absolute is too much
    :param file_path: str, full ptah to QGIS project
    :return: None
    """
    assert file_path is not None, 'You need to provide the full path to thef ile'
    assert file_path != '', 'Invalid "file_path" argument with value %s ' % file_path
    # this is not maybe the best idea...but it will keep us out of trouble
    assert os.path.isabs(file_path), 'The "file_path" has to be an absolute path to avoid trouble'
    assert os.path.exists(file_path), 'The supplied file  "%s" does not exist' % file_path



def introspect(obj=None, namefilter=None, print_out=True):
    """
    Utility function to introspect a given object. Useful to learn about various QGIS classes as they are written in C++ and have limited docs
    :param obj: the object to be intropsected
    :param namefilter: str, if provided, only the public methods that contain the filter wil be handled
    :param print_out: bool, defaults to True, print the methods to stdout, otherwise collect them as a dict
    :return: None of a dict depending on print_out
    """
    assert obj is not None
    if print_out:

        pnames= sorted([e for e in dir(obj) if not (e.startswith('_') or e.endswith('_'))])
        for e in pnames:
            if namefilter:
                if namefilter.lower() in e.lower():

                    m = getattr(obj, e)
                    if callable(m):
                        try:
                            #lets call the fuction woith a carzy arg like an empty dict so it throws exception
                            #the inside exception form the exception we can find details about how to call the function
                            m({})
                        except Exception as ee:
                            ees = str(ee)
                            if not 'overloaded' in ees:
                                if 'argument' in ees:
                                    print '%s :: %s' % (e, ees.split(':')[0].split('argument')[0] )
                                else:
                                    print '%s :: %s' % (e, ees.split(':')[0])
                            else:
                                overloaded =  ees.split('\n')[1:]
                                for c in overloaded:
                                    cc = c.replace('_', '')
                                    print '%s :: %s' % (e, cc.split(':')[0])



                    else:
                        print '%s ' % e

            else:
                #print '%s() :: %s ' % (e, type(getattr(obj, e)))
                m = getattr(obj, e)
                if callable(m):
                    try:
                        # lets call the fuction woith a carzy arg like an empty dict so it throws exception
                        # the inside exception form the exception we can find details about how to call the function
                        m({})
                    except Exception as ee:
                        ees = str(ee)
                        if not 'overloaded' in ees:
                            if 'argument' in ees:
                                print '%s :: %s' % (e, ees.split(':')[0].split('argument')[0])
                            else:
                                print '%s :: %s' % (e, ees.split(':')[0])
                        else:
                            overloaded = ees.split('\n')[1:]
                            for c in overloaded:
                                cc = c.replace('_', '')
                                print '%s :: %s' % (e, cc.split(':')[0])



                else:
                    print '%s ' % e

    else:
        if namefilter:
            return dict([(e, getattr(obj, e)) for e in dir(obj) if
                         not (e.startswith('_') or e.endswith('_') and namefilter.lower() in e.lower())])
        else:
            return dict([(e, getattr(obj, e)) for e in dir(obj) if not (e.startswith('_') or e.endswith('_'))])


def elemnt2xml(elem):
    s = '<%s' % elem.tagName()
    attrs = elem.attributes()
    for i in range(attrs.size()):
        attr = attrs.item(i).toAttr()
        s+= " \"%s\"= \"%s\" " % (attr.name(), attr.value())
    s+='>\n'
    return s + elem.text() + '</%s > ' % elem.tagName()


def isiter(obj):
    try:
        _ = (e for e in obj)
        return True
    except TypeError as e:
        return False


def validate_cfg_dict(d, nd=None, section=None):
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





def mergedicts(dict1, dict2):
    """
    Generatir that merges recursively 2 dicts
    :param dict1:
    :param dict2:
    :return:
    """
    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                yield (k, dict(mergedicts(dict1[k], dict2[k])))
            else:
                # If one of the values is not a dict, you can't continue merging it.
                # Value from second dict overrides one in first and we move on.
                yield (k, dict2[k])
                # Alternatively, replace this with exception raiser to alert you of value conflicts
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])

def traverse(obj):
    if isinstance(obj, dict):
        return {k: traverse(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [traverse(elem) for elem in obj]
    else:
        return obj  # no container, just values (str, int, float)
