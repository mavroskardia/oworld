from zipfile import ZipFile, ZIP_DEFLATED
import configuration
import os

def splitSets(nameList):
    sets = {}
    for name in nameList:
        set = os.path.split(name)[0]
        if not set in sets: sets[set] = []            
        sets[set].append(name)
    return sets

class DatasetBuilder:
    '''Third approach, this time, no nested zip files.'''
    
    def buildDataset(self, path):
        
        zfilename = os.path.join(configuration.datadir, os.path.split(path)[-1] + '.zip')
        
        if os.path.exists(zfilename): os.remove(zfilename)
        
        zf = ZipFile(zfilename, 'w')
        
        for root, dirs, files in os.walk(path):
            if '_svn' in root or '.svn' in root or not files: continue
                        
            pseudoroot = root.replace(path, "")
                        
            for f in files:
                filename = os.path.join(pseudoroot, f)
                zf.write(os.path.join(root, f), filename, ZIP_DEFLATED)
                
        zf.close()
   