from visidata import *
from . import binding as nwn

@VisiData.api
def open_ncs(vd, p):
  return NcsSheet(p.name, source=p)

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
