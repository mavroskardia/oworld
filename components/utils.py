import sys
import traceback
import inspect

class DebugPrint(object):
    """A class to modify how the "print" command works."""
        
    def __init__(self, showMethodNames=False, showLineNumbers=True, out=sys.__stdout__):
        self.out = out
        self.showMethodNames = showMethodNames
        self.showLineNumbers = showLineNumbers
            
    def write(self, string):
        if string == "\n": return
        
        spaces = len(traceback.extract_stack())
        
        try: 
            frame = inspect.currentframe().f_back # get the calling frame
            ls = traceback.extract_stack()[-2]
        except: 
            frame = inspect.currentframe()
            ls = traceback.extract_stack()[-1]
        
        # get the calling class    
        try: 
            c = repr(frame.f_locals['self'])
            c = c[c.find('.')+1:]
            c = c[:c.find(' ')]
        except: 
            c = ls[2]
        
        if self.showLineNumbers: lineNo = " (%s)" % frame.f_lineno
        else: lineNo = ""
        if self.showMethodNames: method = " %s" % ls[2]
        else: method = ""
            
        self.out.write("%s%s%s%s: %s\n" % (" " * spaces, c, method, lineNo, string))
        self.out.flush()
        
    def flush(self):
        self.out.flush()