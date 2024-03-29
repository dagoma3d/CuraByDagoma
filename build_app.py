# coding=utf-8
import sys
import os

if sys.platform.startswith('darwin'):
    from setuptools import setup

    release_version = os.environ['RELEASE_VERSION']
    build_version = os.environ['BUILD_VERSION']
    build_name = os.environ['BUILD_NAME']

    APP = ['Cura/cura.py']
    DATA_FILES = ['Cura/LICENSE', 'resources/example', 'resources/images', 'resources/locale', 'resources/meshes', 'resources/printers', 'resources/xml', 'plugins']
    PLIST = {
        u'CFBundleName': build_name,
        u'CFBundleDisplayName': build_name,
        u'CFBundleShortVersionString': release_version,
        u'CFBundleVersion': build_version,
        u'CFBundleIdentifier': u'com.Dagoma.'+ build_name + build_version,
        u'LSMinimumSystemVersion': u'10.9',
        u'LSApplicationCategoryType': u'public.app-category.graphics-design',
        u'CFBundleDocumentTypes': [
            {
                u'CFBundleTypeRole': u'Viewer',
                u'LSItemContentTypes': [u'com.pleasantsoftware.uti.stl'],
                u'LSHandlerRank': u'Owner',
                },
            {
                u'CFBundleTypeRole': u'Viewer',
                u'LSItemContentTypes': [u'org.khronos.collada.digital-asset-exchange'],
                u'LSHandlerRank': u'Owner'
            },
            {
                u'CFBundleTypeName': u'Wavefront 3D Object',
                u'CFBundleTypeExtensions': [u'obj'],
                u'CFBundleTypeMIMETypes': [u'application/obj-3d'],
                u'CFBundleTypeRole': u'Viewer',
                u'LSHandlerRank': u'Owner'
            }
        ],
        u'UTImportedTypeDeclarations': [
            {
                u'UTTypeIdentifier': u'com.pleasantsoftware.uti.stl',
                u'UTTypeConformsTo': [u'public.data'],
                u'UTTypeDescription': u'Stereo Lithography 3D object',
                u'UTTypeReferenceURL': u'http://en.wikipedia.org/wiki/STL_(file_format)',
                u'UTTypeTagSpecification': {u'public.filename-extension': [u'stl'], u'public.mime-type': [u'text/plain']}
            },
            {
                u'UTTypeIdentifier': u'org.khronos.collada.digital-asset-exchange',
                u'UTTypeConformsTo': [u'public.xml', u'public.audiovisual-content'],
                u'UTTypeDescription': u'Digital Asset Exchange (DAE)',
                u'UTTypeTagSpecification': {u'public.filename-extension': [u'dae'], u'public.mime-type': [u'model/vnd.collada+xml']}
            },
            {
                u'UTTypeIdentifier': u'com.ultimaker.obj',
                u'UTTypeConformsTo': [u'public.data'],
                u'UTTypeDescription': u'Wavefront OBJ',
                u'UTTypeReferenceURL': u'https://en.wikipedia.org/wiki/Wavefront_.obj_file',
                u'UTTypeTagSpecification': {u'public.filename-extension': [u'obj'], u'public.mime-type': [u'text/plain']}
            },
            {
                u'UTTypeIdentifier': u'com.ultimaker.amf',
                u'UTTypeConformsTo': [u'public.data'],
                u'UTTypeDescription': u'Additive Manufacturing File',
                u'UTTypeReferenceURL': u'https://en.wikipedia.org/wiki/Additive_Manufacturing_File_Format',
                u'UTTypeTagSpecification': {u'public.filename-extension': [u'amf'], u'public.mime-type': [u'text/plain']}
            }
        ]
    }
    OPTIONS = {
        'argv_emulation': True,
        'iconfile': 'resources/images/cura.icns',
        'includes': ['objc', 'Foundation'],
        'resources': DATA_FILES,
        'optimize': '2',
        'plist': PLIST,
        'bdist_base': 'scripts/darwin/build',
        'dist_dir': 'scripts/darwin/dist'
    }

    setup(
        name=build_name,
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app']
    )
else:
   print('No build_app implementation for your system.')
