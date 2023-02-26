switch("threads", "on")
switch("app", "lib")

# always build against neverwinter.nim with zlib for nwsync repo extract
switch("d", "zlib")

when defined(windows):
  switch("tlsEmulation", "off")
  switch("passL", "-static")
