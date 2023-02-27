from visidata import *
from . import binding as nwn

from .gff import *
from .erf import *
from .key import *
from .nwscript import *
from .nwsync import *
from .res import *
from .ssf import *
from .tlk import *
from .twoda import *

# sq3 extension is just sqlite

@VisiData.api
def open_sq3(vd, p):
  return vd.openSource(p, filetype='sqlite')

# Freestanding API

def decompress(magic, data):
  # Note how we swap args to match the SQL function.
  return nwn.decompressBuf(data, magic)

def compress(magic, data):
  # Note how we swap args to match the SQL function.
  return nwn.compressBuf(bytes(data, 'utf-8'), str(magic))

