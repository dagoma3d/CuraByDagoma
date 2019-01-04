"""
Helper module to check sha256 sum.
"""
__copyright__ = "Copyright (C) 2019 Dagoma - Released under terms of the AGPLv3 License"

import os
import urllib2

official_version = None
try:
	official_version = urllib2.urlopen("https://dist.dagoma3d.com/version/CuraByDagoma").read()
except:
	pass

def isLatest():
	return official_version is None or official_version == os.environ['CURABYDAGO_RELEASE_VERSION']
