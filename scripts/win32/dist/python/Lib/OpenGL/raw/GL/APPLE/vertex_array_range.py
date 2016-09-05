'''OpenGL extension APPLE.vertex_array_range

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_APPLE_vertex_array_range'
_DEPRECATED = False
GL_VERTEX_ARRAY_RANGE_APPLE = constant.Constant( 'GL_VERTEX_ARRAY_RANGE_APPLE', 0x851D )
GL_VERTEX_ARRAY_RANGE_LENGTH_APPLE = constant.Constant( 'GL_VERTEX_ARRAY_RANGE_LENGTH_APPLE', 0x851E )
glget.addGLGetConstant( GL_VERTEX_ARRAY_RANGE_LENGTH_APPLE, (1,) )
GL_VERTEX_ARRAY_STORAGE_HINT_APPLE = constant.Constant( 'GL_VERTEX_ARRAY_STORAGE_HINT_APPLE', 0x851F )
GL_VERTEX_ARRAY_RANGE_POINTER_APPLE = constant.Constant( 'GL_VERTEX_ARRAY_RANGE_POINTER_APPLE', 0x8521 )
GL_STORAGE_CACHED_APPLE = constant.Constant( 'GL_STORAGE_CACHED_APPLE', 0x85BE )
GL_STORAGE_SHARED_APPLE = constant.Constant( 'GL_STORAGE_SHARED_APPLE', 0x85BF )
glVertexArrayRangeAPPLE = platform.createExtensionFunction( 
'glVertexArrayRangeAPPLE',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLsizei,ctypes.c_void_p,),
doc='glVertexArrayRangeAPPLE(GLsizei(length), c_void_p(pointer)) -> None',
argNames=('length','pointer',),
deprecated=_DEPRECATED,
)

glFlushVertexArrayRangeAPPLE = platform.createExtensionFunction( 
'glFlushVertexArrayRangeAPPLE',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLsizei,ctypes.c_void_p,),
doc='glFlushVertexArrayRangeAPPLE(GLsizei(length), c_void_p(pointer)) -> None',
argNames=('length','pointer',),
deprecated=_DEPRECATED,
)

glVertexArrayParameteriAPPLE = platform.createExtensionFunction( 
'glVertexArrayParameteriAPPLE',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,),
doc='glVertexArrayParameteriAPPLE(GLenum(pname), GLint(param)) -> None',
argNames=('pname','param',),
deprecated=_DEPRECATED,
)


def glInitVertexArrayRangeAPPLE():
    '''Return boolean indicating whether this extension is available'''
    return extensions.hasGLExtension( EXTENSION_NAME )
