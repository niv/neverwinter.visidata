# Package

version       = "0.1.0"
author        = "Bernhard Stoeckner <n@e-ix.net>"
description   = "A new awesome nimble package"
license       = "MIT"

when defined(posix):
  bin = @["binding.so"]
elif defined(windows):
  bin = @["binding.pyd"]
else:
  {.fatal: "?os?".}

# Dependencies

requires "nim >= 1.6.0"
requires "neverwinter >= 1.5.8"
requires "nimpy >= 0.2.0"
requires "zip >= 0.3.1"
