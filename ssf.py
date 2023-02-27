from visidata import *
from . import binding as nwn

@VisiData.api
def open_ssf(vd, p):
  return SsfSheet(p.name, source=p)

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