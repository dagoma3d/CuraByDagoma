from OpenGL.platform import GLUT, CurrentContextIsValid, GLUT_GUARD_CALLBACKS
from OpenGL import contextdata, error, platform, logs
from OpenGL.raw import GLUT as simple
from OpenGL._bytes import bytes, _NULL_8_BYTE, as_8_bit
import ctypes, os, sys, traceback
PLATFORM = platform.PLATFORM
FUNCTION_TYPE = simple.CALLBACK_FUNCTION_TYPE

log = logs.getLog( 'OpenGL.GLUT.special' )

#_simple_glutInit = getattr(simple, 'glutInit')
#print _simple_glutInit
#_base_glutInit = getattr(GLUT, 'glutInit')
#print _base_glutInit

print 'GLUT :'
print GLUT
print '**********'
print 'CurrentContextIsValid :'
print CurrentContextIsValid
print '**********'
print 'GLUT_GUARD_CALLBACKS :'
print GLUT_GUARD_CALLBACKS
print '**********'
print 'GLUT as simple :'
print simple
print '**********'
