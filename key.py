from visidata import *
from . import binding as nwn
from .res import *

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
