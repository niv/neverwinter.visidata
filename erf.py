from visidata import *
from . import binding as nwn
from .res import *

@VisiData.api
def open_erf(vd, p):
  return ErfSheet(p.name, source=p)

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
