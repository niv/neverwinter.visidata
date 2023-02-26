import pathlib
import tempfile
import requests
from visidata import *

from . import binding as nwn

def _writeNimPayload(path, data):
  'Helper to write out a nim-ish str/bytes affair'
  with visidata.Path.open_bytes(path, mode='wb') as fp:
    if isinstance(data, str):
      # Incoming string data is always expected to be encoded as utf-8.
      # However, this helper is currently not expected to be called for string payloads.
      # Revisit if this fail is ever hit.
      raise ValueError("?? READ CODE don't write strings this way ??")
      fp.write(bytes(data, 'utf-8'))
    else:
      fp.write(data)

class NwnResTable(Sheet):
  def extract(self, *rows, path=None):
    path = path or pathlib.Path('.')

    for row in rows:
      if (path/row[0]).exists():
        vd.confirm(f'{row[0]} exists, overwrite? ')  #1452
    self.extract_async(*rows, path=path)

  @asyncthread
  def extract_async(self, *rows, path=None):
    'Extract rows to *path*, without confirmation.'
    path = path or pathlib.Path('.')
    for r in Progress(rows):
      # VIRTUALS:
      file = self.get_filename(r)
      data = self.get_data(r)
      _writeNimPayload(Path(str(path) + "/" + file), data)
      vd.status(f'extracted {file}')

  def openRow(self, row):
    name = self.get_filename(row)
    namepair = os.path.splitext(os.path.basename(name))
    data = self.get_data(row)

    # WAR: attempt to detect compressed sqlite databases (e.g. module.sq3)
    if namepair[1] == ".sq3" and data[0:4] == b'SQL3':
      data = nwn.decompressBuf(data, magic="SQL3")

    tmp = tempfile.NamedTemporaryFile(prefix=namepair[0], suffix=namepair[1])
    pa = Path(tmp.name)
    _writeNimPayload(pa, data)
    pa.openSourceTmpFile = tmp # keep alive as long as source is open
    sheet = vd.openSource(pa, filetype=namepair[1][1:])
    sheet.name = self.name + '/' + namepair[0]
    vd.push(sheet)

NwnResTable.addCommand('x', 'extract-file', 'extract(cursorRow)', 'extract current file to current directory')
NwnResTable.addCommand('gx', 'extract-selected', 'extract(*onlySelectedRows)', 'extract selected files to current directory')
NwnResTable.addCommand('zx', 'extract-file-to', 'extract(cursorRow, path=inputPath("extract to dir: "))', 'extract current file to given directory')
NwnResTable.addCommand('gzx', 'extract-selected-to', 'extract(*onlySelectedRows, path=inputPath("extract %d files to dir: " % nSelectedRows))', 'extract selected files to given directory')

vd.addMenu(Menu('File', Menu('Extract',
        Menu('current file', 'extract-file'),
        Menu('current file to', 'extract-file-to'),
        Menu('selected files', 'extract-selected'),
        Menu('selected files to', 'extract-selected-to'),
    )))

# TwoDA

@VisiData.api
def open_2da(vd, p): return TwoDASheet(p.name, source=p)
@VisiData.api
def save_2da(vd, p, *vs):
  if len(vs) != 1: vd.fail("only one sheet supported")

  def get_rows(sheet, cols):
      for row in Progress(sheet.rows):
          yield [ col.getDisplayValue(row) for col in cols ]

  # Data passed IN is utf-8, returned data is a bytes array already in NWN encoding.
  tdabytes = nwn.dumpTwoda(
      [ col.name for col in vs[0].visibleCols ],
      list(get_rows(vs[0], vs[0].visibleCols))
  )

  with p.open_bytes(mode='w') as fp:
    fp.write(tdabytes)
    vd.status(f'wrote {p.given}')

class TwoDASheet(SequenceSheet):
  def iterload(self):
    self.twoda = nwn.openTwoda(str(self.source))
    yield nwn.twodaGetColumns(self.twoda)
    for row in Progress(nwn.twodaGetAllRows(self.twoda)):
      yield row

# TLK

@VisiData.api
def open_tlk(vd, p): return TlkSheet(p.name, source=p)
@VisiData.api
def save_tlk(vd, p, *vs):
  if len(vs) != 1: vd.fail("only one sheet per TLK supported")
  vs = vs[0]

  def get_rows(sheet, cols):
      for row in Progress(sheet.rows):
          yield [ col.getTypedValue(row) for col in cols ]

  if len(vs.visibleCols) != 4:
    vd.fail("column count mismatch, expect 4 (STRREF, TEXT, SOUNDRESREF, SOUNDLENGTH)")

  tlkrows = []
  for row in Progress(vs.rows):
    tlkrows.append((int(row[0]), str(row[1]), str(row[2]), float(row[3])))

  tlkbytes = nwn.dumpTlk(tlkrows)

  with p.open_bytes(mode='w') as fp:
    fp.write(tlkbytes)
    vd.status(f'wrote {p.given}')

class TlkSheet(Sheet):
  columns = [
    ColumnItem("strref", 0, type=int),
    ColumnItem("text", 1),
    ColumnItem("soundresref", 2),
    ColumnItem("soundlength", 3, type=float),
  ]
  def iterload(self):
    tlk = nwn.openTlk(str(self.source))
    for row in nwn.tlkGetRows(tlk):
      yield row

# ERF

@VisiData.api
def open_erf(vd, p): return ErfSheet(p.name, source=p)
VisiData.open_hak = VisiData.open_erf
VisiData.open_mod = VisiData.open_erf
VisiData.open_nwm = VisiData.open_erf
VisiData.open_sav = VisiData.open_erf

# No writing yet!

class ErfSheet(NwnResTable):
  columns = [
    ColumnItem("resref", 0),
    ColumnExpr("ext", 'resref.split(".")[1]'),
    ColumnItem("size", 1, type=int),
  ]

  def iterload(self):
    self.erf = nwn.openErf(str(self.source))
    for row in nwn.erfGetContent(self.erf):
      yield row
  def get_filename(self, row):
    return row[0]

  def get_data(self, row):
    return nwn.erfGetResData(self.erf, row[0])

# NWSync

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
      response = requests.get(self.source.given, stream=True, **vd.options.getall('http_req_'))
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
      response = requests.get(dataUrl, stream=True, **vd.options.getall('http_req_'))
      response.raise_for_status()
      content = response.content
    else:
      datafile = Path(self.basePath + "/" + dataPath)
      content = Path.read_bytes(datafile)

    return nwn.decompressBuf(content, magic="NSYC")

# KEYTABLE

@VisiData.api
def open_key(vd, p):
  return KeyTable(p.name, source=p)

class KeyTable(NwnResTable):
  columns = [
    ColumnItem("resref", 0),
    ColumnExpr("ext", 'resref.split(".")[1]'),
    ColumnItem("iosize", 1, type=int),
    ColumnItem("bif", 2),
  ]

  def iterload(self):
    self.key = nwn.openKey(self.source.given)
    for row in nwn.keyGetContent(self.key):
      yield row

  def get_filename(self, row):
    return row[0]

  def get_data(self, row):
    return nwn.keyGetResData(self.key, row[0])

# GFF

# Not really sure how to present this best in a tabular format.
# This is just a experiment. Future improvements chould use expandable
# visidata sections instead of nesting paths with "."?

@VisiData.api
def open_gff(vd, p): return GffTable(p.name, source=p)
VisiData.open_utc = open_gff
VisiData.open_utd = open_gff
VisiData.open_ute = open_gff
VisiData.open_uti = open_gff
VisiData.open_utm = open_gff
VisiData.open_utp = open_gff
VisiData.open_uts = open_gff
VisiData.open_utt = open_gff
VisiData.open_utw = open_gff
VisiData.open_git = open_gff
VisiData.open_are = open_gff
VisiData.open_gic = open_gff
VisiData.open_ifo = open_gff
VisiData.open_fac = open_gff
VisiData.open_dlg = open_gff
VisiData.open_itp = open_gff
VisiData.open_bic = open_gff
VisiData.open_jrl = open_gff
VisiData.open_gui = open_gff

class GffTable(Sheet):
  columns = [
    ColumnItem("PATH", 0),
    ColumnItem("TYPE", 1),
    ColumnItem("VALUE", 2),
  ]

  def iterload(self):
    gff = nwn.readGff(self.source.given)
    for row in gff:
      yield row

# SSF

@VisiData.api
def open_ssf(vd, p): return SsfSheet(p.name, source=p)
@VisiData.api
def save_ssf(vd, p, *vs):
  if len(vs) != 1: vd.fail("only one sheet supported")
  vs = vs[0]

  def get_rows(sheet, cols):
      for row in Progress(sheet.rows):
          yield [ col.getDisplayValue(row) for col in cols ]

  if len(vs.visibleCols) != 2:
    vd.fail("column count mismatch, expect 2 (resref:str, strref:int)")

  ssfrows = []
  for row in Progress(vs.rows):
    ssfrows.append((str(row[0]), int(row[1])))

  ssfbytes = nwn.dumpSsf(ssfrows)

  with p.open_bytes(mode='w') as fp:
    fp.write(ssfbytes)
    vd.status(f'wrote {p.given}')

class SsfSheet(Sheet):
  columns = [
    ItemColumn("resref", 0),
    ItemColumn("strref", 1, type=int),
  ]
  def iterload(self):
    data = self.source.read_bytes()
    lines = nwn.readSsf(data)
    for line in lines:
      yield line

# NCS

@VisiData.api
def open_ncs(vd, p): return NcsSheet(p.name, source=p)

class NcsSheet(Sheet):
  columns = [
    ItemColumn("offset", 0, type=int),
    ItemColumn("op", 1, type=int),
    ItemColumn("aux", 2, type=int),
    ItemColumn("extra", 3),
    ItemColumn("disasm", 4),
  ]
  def iterload(self):
    data = self.source.read_bytes()
    lines = nwn.disasmNcs(data)
    for line in lines:
      yield line

# game sq3 glue

@VisiData.api
def open_sq3(vd, p): return vd.openSource(p, filetype='sqlite')

# Freestanding API

def decompress(magic, data):
  # Note how we swap args to match the SQL function.
  return nwn.decompressBuf(data, magic)

def compress(magic, data):
  # Note how we swap args to match the SQL function.
  return nwn.compressBuf(bytes(data, 'utf-8'), str(magic))
