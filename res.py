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
