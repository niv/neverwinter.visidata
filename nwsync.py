from visidata import *
from . import binding as nwn
from .res import *

import requests

@VisiData.api
def open_nwsyncmanifest(vd, p):
  return NWSyncManifestSheet(p.name, source=p)

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
      response = requests.get(self.source.given, **vd.options.getall('http_req_'))
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
      response = requests.get(dataUrl, **vd.options.getall('http_req_'))
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
    response = requests.get("https://api.nwn.beamdog.net/v1/servers", **vd.options.getall('http_req_'))
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