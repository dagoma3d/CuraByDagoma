"""
Helper module to check sha256 sum.
"""
__copyright__ = "Copyright (C) 2019 Dagoma - Released under terms of the AGPLv3 License"

import os
import urllib2

official_version = urllib2.urlopen("https://dist.dagoma3d.com/version/CuraByDagoma").read()

def isLatest():
	print official_version
	print os.environ['CURABYDAGO_RELEASE_VERSION']
	return official_version == os.environ['CURABYDAGO_RELEASE_VERSION']
