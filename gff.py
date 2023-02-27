from visidata import *
from . import binding as nwn

# Not really sure how to present this best in a tabular format.
# This is just a experiment. Future improvements chould use expandable
# visidata sections instead of nesting paths with "."?

@VisiData.api
def open_gff(vd, p):
  return GffTable(p.name, source=p)

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
