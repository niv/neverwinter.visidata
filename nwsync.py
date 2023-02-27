from visidata import *
from . import binding as nwn
from .res import *

import requests
import requests_cache
from datetime import timedelta
from urllib.parse import urlparse
import re

@VisiData.api
def open_nwsyncmanifest(vd, p):
  return NWSyncManifestSheet(p.name, source=p)

def _create_key(request: requests.PreparedRequest, **kwargs) -> str:
  # Attempt to match out the hash of the data file
  fragments = urlparse(request.url).path.split("/")
  # data sha1 AA BB AABBCCDD..
  # manifests AABBCCDD..
  if ((len(fragments) >= 5 and fragments[-5] == "data" and fragments[-4] == "sha1") or
      (len(fragments) >= 2 and fragments[-2] == "manifests")):
    file = fragments[-1]
    if re.fullmatch("^[a-z0-9]+$", file):
      return file
  return requests_cache.cache_keys.create_key(request, **kwargs)

_http_cache = requests_cache.CachedSession(
  nwn.findUserRoot() + '/visidata_http_cache.sqlite3',
  key_fn=_create_key,
  cache_control=False,
  backend='sqlite',
  urls_expire_after = {
    # currently not caching these too long, still seems wasteful
    '*/data/sha1/??/??/*': timedelta(days=3),
    '*/manifests/*': timedelta(weeks=4),
    '*': requests_cache.DO_NOT_CACHE
  }
)

vd.addGlobals({
  # only way i could find to expose this to expr columns
  "nwsync_http_cache": _http_cache
})

class NWSyncManifestSheet(NwnResTable):
  columns = [
    ColumnItem("resref", 0),
    ColumnExpr("ext", 'resref.split(".")[1]'),
    ColumnItem("size", 1, type=int),
    ColumnItem("sha1", 2),
  ]

  basePath = ""
  baseUrl = ""

  def iterload(self):
    if self.source.is_url():
      parsed = urlparse(self.source.given)
      basePath = parsed.path[0: parsed.path.rfind("/manifests/")]
      self.baseUrl = parsed._replace(path=basePath).geturl()
      response = _http_cache.get(self.source.given, **vd.options.getall('http_req_'))
      response.raise_for_status()
      self.manifest = nwn.readManifest(response.content)
    else:
      self.basePath = str(os.path.dirname(self.source)) + "/../"
      self.manifest = nwn.openManifest(self.source.given)

    for row in nwn.manifestGetContent(self.manifest):
      yield row

  def get_filename(self, row):
    return row[0]

  def get_data(self, row):
    content = b""
    sha = row[2]
    dataPath = "data/sha1/" + sha[0:2] + "/" + sha[2:4] + "/" + sha
    if self.baseUrl != "":
      dataUrl = self.baseUrl + "/" + dataPath
      response = _http_cache.get(dataUrl, **vd.options.getall('http_req_'))
      response.raise_for_status()
      content = response.content
    else:
      datafile = Path(self.basePath + "/" + dataPath)
      content = Path.read_bytes(datafile)

    return nwn.decompressBuf(content, magic="NSYC")

@VisiData.api
def openurl_nwsync(vd, p, filetype=None):
  if p.given == "nwsync://":
    return NWSyncSwarmSheet()
  else:
    vd.fail("Syntax: nwsync://[?] not supported yet")

class NWSyncSwarmSheet(Sheet):
  columns = [
    ItemColumn("host", 0),
    ItemColumn("sha1", 1),
    ExprColumn("cached", 'nwsync_http_cache.cache.contains(sha1)'),
    ItemColumn("servers", 2),
  ]

  test = 1

  def __init__(self):
    super().__init__("nwsyncswarm")

  def openRow(self, row):
    url = row[0] + "/manifests/" + row[1]
    vd.push(vd.openSource(url, filetype='nwsyncmanifest'))

  def iterload(self):
    self.setKeys([self.columns[0], self.columns[1]])
    response = _http_cache.get("https://api.nwn.beamdog.net/v1/servers", **vd.options.getall('http_req_'))
    response.raise_for_status()
    servers = []
    for server in response.json():
      if server.get('nwsync') and len(server['nwsync']['manifests']) == 1:#
        found = False
        url = server['nwsync']['url']
        sha1 = server['nwsync']['manifests'][0]['hash']
        name = server['session_name']

        for existing in servers:
          if existing[0] == url and existing[1] == sha1:
            existing[2].append(name)
            found = True
            break

        if not found:
          servers.append([url, sha1, [name]])

    for server in servers:
      yield server