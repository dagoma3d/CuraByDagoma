"""
Helper module to check sha256 sum.
"""
__copyright__ = "Copyright (C) 2019 Dagoma - Released under terms of the AGPLv3 License"

import os
from urllib.request import urlopen
import json
from pkg_resources import parse_version

def isLatest():
	try:
		release_url = "https://api.github.com/repos/dagoma3d/CuraByDagoma/releases/latest"
		response = urlopen(release_url)
		official_version = json.loads(response.read())['tag_name']
		#print("official_version: ", official_version)
		return parse_version(os.environ['CURABYDAGO_RELEASE_VERSION']) >= parse_version(official_version)
	except:
		return True # if we can't check the version, we assume it's the latest
