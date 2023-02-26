# Changelog

## [Unreleased]

### Added

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
