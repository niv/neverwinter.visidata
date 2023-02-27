from visidata import *
from . import binding as nwn

@VisiData.api
def open_2da(vd, p):
  return TwoDASheet(p.name, source=p)

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
