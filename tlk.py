from visidata import *
from . import binding as nwn

@VisiData.api
def open_tlk(vd, p):
  return TlkSheet(p.name, source=p)

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
