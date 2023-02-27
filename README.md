# VisiData NWN file format support

This adds support to [VisiData](https://visidata.org) for the following Neverwinter Nights: Enhanced Edition file formats:

- Erf (hak, mod, nwm, sav): Browsing and extracting
- KeyBif: Browsing and extracting
- TwoDA: Reading and saving
- Tlk: Reading and saving
- NWSync Manifests: Opening from local disk or HTTP, browsing and extracting. Currently requires giving a explicit filetype:
  - `vd -f nwsyncmanifest http://..../manifests/aabbccdd..`
  - This may change in the future, depending on if VisiData/http can be taught to guess the filetype based on magic bytes.
- Gff: Transform into flat list and allow browsing (Highly experimental and subject to change)
- Ssf: Reading and saving
- Ncs: Print a simple disassembly

## Install

- Requires VisiData (tested against 2.11)
- Requires nim compiler suite installed (tested against 1.6.10)
- Clone this repository into `~/.visidata/plugins/neverwinter`
- Build bindings locally (do this every time you update the plugin code):
    - `nimble build -d:release`
- Install python-side dependencies:
   - `pip3 install -r requirements.txt`
- Add this line to `~/.visidata/plugins/__init__.py`:
    - `import plugins.neverwinter`

## API additions

- `neverwinter.decompress(magic, data)`
- `neverwinter.compress(magic, data)`

## Misc

### TwoDA line numbers

Add this to `~/.visidatarc` to make the currently-selected row show up in the bottom right:

    options.disp_rstatus_fmt += ' {sheet.cursorRowIndex}'

### Decompress nwcompressedbuf columns

When viewing a sqlite DB that has a compressed row, you can decompress it like so:

Press `=` to add a expr/derived column, and add the following python code:

```python
neverwinter.decompress('RESF', my_column)
```

Replace `my_column` with the column to decompress and `'RESF'` with the expected magic bytes:

* `SQL3`: embedded sqlite3 datbases in erf
* `RESF`: CampaignDB compressed strings/voids.
* `NSYC`: NWSync compressed file.

Hint: View errors with `z^E` on the cell that errors out. `U` to undo.
