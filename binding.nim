import std/[streams, sets, strutils, sequtils, options, os, tables, uri]
import std/[asyncdispatch, asyncnet, nativesockets, json, jsonutils]

import neverwinter/[tlk, erf, key, gff, twoda, nwsync, ssf]
import neverwinter/nwscript/nwasm
import neverwinter/[resref, resman, compressedbuf, game]

import nimpy

# All binary data needs to be passed as seq[bytes], all string data as string.
# string data needs to be encoded utf-8.
# bytes data is passed as-is with no re-encoding, so it'll be whatever encoding NWN is set at.

proc toStr(str: seq[byte]): string =
  result = newString(len(str))
  for idx, ch in str:
    result[idx] = char(str[idx])

proc toBytes(str: string): seq[byte] =
  result = newSeq[byte](str.len)
  for idx, ch in str:
    result[idx] = byte(ch)

proc decompressBuf*(data: seq[byte], magic: string): seq[byte] {.exportpy.} =
  toBytes decompress(toStr(data), makeMagic(magic))

proc compressBuf*(data: seq[byte], magic: string): seq[byte] {.exportpy.} =
  toBytes compress(toStr(data), Algorithm.Zstd, makeMagic(magic))

proc findUserRoot*(): string {.exportpy.} = game.findUserRoot()

proc findNwnRoot*(): string {.exportpy.} = game.findNwnRoot()

# =======
# Key

proc openKey*(fn: string): KeyTable {.exportpy.} =
  let base = splitFile(fn).dir
  readKeyTable(openFileStream(fn), "") do (bif: string) -> Stream:
    openFileStream(base / ".." / bif)

type KeyEntry* = tuple
  resref: string
  ioSize: int
  bif: string

proc keyGetContent*(key: KeyTable): seq[KeyEntry] {.exportpy.} =
  for bif in key.bifs:
    var bifname = bif.filename
    bifname.removePrefix("data/")
    for r in getVariableResources(bif):
      result.add((
        resref: $r.resref,
        ioSize: r.ioSize,
        bif: bifName,
      ).KeyEntry)

proc keyGetResData*(key: KeyTable, resref: string): seq[byte] {.exportpy.} =
  let rr = key.demand(newResolvedResRef(resref))
  toBytes rr.readAll()

# =======
# Erf

proc openErf*(fn: string): Erf {.exportpy.} =
  readErf(openFileStream(fn), fn)

type ErfEntry* = tuple
  filename: string
  size: int

proc erfGetContent*(erf: Erf): seq[ErfEntry] {.exportpy.} =
  for r in erf.contents:
    let rr = erf.demand(r)
    result.add((
      filename: $r,
      size: uncompressedSize(rr)
    ).ErfEntry)

proc erfGetResData*(erf: Erf, resref: string): seq[byte] {.exportpy.} =
  toBytes erf.demand(newResolvedResRef(resref)).readAll()

# =======
# 2da

proc readTwoda*(data: seq[byte]): TwoDA {.exportpy.} =
  readTwoDA(newStringStream(toStr data))

proc openTwoda*(fn: string): TwoDA {.exportpy.} =
  readTwoDA(openFileStream(fn))

proc twodaGetAllRows*(tda: TwoDA): seq[seq[string]] {.exportpy.} =
  tda.rows.mapIt(it.mapIt(it.get("")))

proc twodaGetColumns*(tda: TwoDA): seq[string] {.exportpy.} =
  tda.columns

proc dumpTwoda*(columns: seq[string], rows: seq[seq[string]]): seq[byte] {.exportpy.} =
  var s = newStringStream()
  var tda = newTwoDA()
  tda.columns = columns
  for r in rows:
    # rows[] is utf8 data. writeTwoDA() does the conversion to charset
    tda[tda.len] = r.mapIt(if it != "": some(it) else: none(string))
  s.writeTwoDA(tda)
  s.setPosition(0)
  toBytes s.readAll()

# ======
# nwsync

proc openManifest*(fn: string): Manifest {.exportpy.} =
  readManifest(openFileStream(fn))

proc readManifest*(data: string): Manifest {.exportpy.} =
  readManifest(newStringStream(data))

proc manifestGetContent*(mf: Manifest): seq[(string, int, string)] {.exportpy.} =
  mf.entries.mapIt(($it.resref, int it.size, it.sha1))

# ======
# TLK

# strref, text, soundref, soundlen
type PyTlkEntry = (int, string, string, float)

proc openTlk*(fn: string): SingleTlk {.exportpy.} =
  readSingleTlk(openFileStream(fn), useCache = false)

proc tlkGetRows*(tlk: SingleTlk): seq[PyTlkEntry] {.exportpy.} =
  # result = newSeq[PyTlkEntry](tlk.highest+1)
  for i in 0..tlk.highest:
    let e = tlk[i.StrRef]
    if e.isSome:
      let ee = e.unsafeGet
      result.add((i, ee.text, ee.soundResRef, ee.soundLength))

proc dumpTlk*(entries: seq[PyTlkEntry]): seq[byte] {.exportpy.} =
  var s = newStringStream()
  var tlk = newSingleTlk()
  for e in entries:
    tlk[StrRef e[0]] = TlkEntry(text: e[1], soundResRef: e[2], soundLength: e[3])
  s.writeTlk(tlk)
  s.setPosition(0)
  toBytes s.readAll()

# ======
# GFF

# path, type, value
type GffRepr = seq[(string, string, string)]

proc addList(list: GffList, pa: seq[string], into: var GffRepr)

proc addStruct(struct: GffStruct, pa: seq[string], into: var GffRepr) =
  for k, v in struct.fields:
    let pa = pa.concat(@[k])
    var str = ""
    case v.fieldKind
    of GffFieldKind.Struct:
      addStruct(v.getValue(GffStruct), pa, into)
      continue
    of GffFieldKind.List:
      addList(v.getValue(GffList), pa, into)
      continue
    of GffFieldKind.Byte:  str = $v.getValue(GffByte)
    of GffFieldKind.Char:  str = $v.getValue(GffChar)
    of GffFieldKind.Word:  str = $v.getValue(GffWord)
    of GffFieldKind.Short:  str = $v.getValue(GffShort)
    of GffFieldKind.Dword:  str = $v.getValue(GffDword)
    of GffFieldKind.Int:  str = $v.getValue(GffInt)
    of GffFieldKind.Float:  str = $v.getValue(GffFloat)

    of GffFieldKind.Dword64: str = $v.getValue(GffDword64)
    of GffFieldKind.Int64: str = $v.getValue(GffInt64)
    of GffFieldKind.Double: str = $v.getValue(GffDouble)
    of GffFieldKind.CExoString: str = $v.getValue(GffCExoString)
    of GffFieldKind.ResRef: str = $v.getValue(GffResRef)
    of GffFieldKind.CExoLocString: str = $v.getValue(GffCExoLocString)
    of GffFieldKind.Void: str = $v.getValue(GffVoid)

    into.add((pa.join("."), $v.fieldKind, str))

proc addList(list: GffList, pa: seq[string], into: var GffRepr) =
  for idx, e in list:
    addStruct(e, pa.concat(@[$idx]), into)

proc readGff*(fn: string): GffRepr {.exportpy.} =
  let root = readGffRoot(openFileStream(fn), false)
  addStruct(root, @[], result)

# ======
# ssf

# (resref, strref)
proc readSsf*(ssf: seq[byte]): seq[(string, int)] {.exportpy.} =
  let s = readSsf(newStringStream(toStr(ssf)))
  for e in s.entries:
    result.add((e.resref, e.strref.int))

proc dumpSsf*(rows: seq[(string, int)]): seq[byte] {.exportpy.} =
  let st = newStringStream()
  var s = newSsf()
  for r in rows:
    s.entries.add(SsfEntry(resref: r[0], strref: r[1].StrRef))
  writeSsf(st, s)
  st.setPosition(0)
  toBytes st.readAll()

# ======
# ncs

proc disasmNcs*(ncs: seq[byte]): seq[(int, int, int, string, string)] {.exportpy.} =
  let ii = disAsm(newStringStream(toStr(ncs)))

  var offset = 0
  for idx, c in ii:
    result.add((offset, c.op.int, c.aux.int, c.extra.escape("", ""), $c))
    inc offset, c.len
