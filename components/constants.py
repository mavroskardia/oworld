# constants.py
# All global constants eventually find their way here.
# by Andrew Martin (2006)
#
# TODO:
#    [] Comment all classes
#    [] Rename members that don't adhere to style guidelines
#    [] Review algorithms to determine if there is a more pythonic way
#    [] Review classes invluded in module for relevance to module
#

class BitClass(object):
    
    def value(cls, attr): return getattr(cls, attr)
    value = classmethod(value)
    def attr(cls, value): 
        for attrib in cls.__dict__.keys():
            if getattr(cls, attrib) == value: return attrib
        return None
    attr = classmethod(attr)
    
    def attributeList(cls, values):
        ret = []
        for attrib in cls.__dict__.keys():
            v = getattr(cls, attrib)      
            if isinstance(v, int) and (v & values == v): ret.append(attrib)
        return ret
    attributeList = classmethod(attributeList)

class EquipLocation(BitClass):
    """Equippable item locations."""
    Not_Equippable, One_Handed, Two_Handed = 1, 2, 4
    
class EquipTypes(BitClass):
    """Equipment types. It is possible to have more than one of these"""
    Not_Attack, Melee, Ranged = 1, 2, 4
    
class JobTypes(BitClass):
    """Job types. It is possible to have more than one of these"""
    All, Jobless, Fighter, Lover = 1, 2, 4, 8

if __name__ == '__main__':
    
    print 'Testing BitClass'

    print 'EquipLocation.attr(0): %s' % EquipLocation.attr(0)
    print 'EquipLocation.value("NonEquippable"): %s' % EquipLocation.value('NonEquippable')