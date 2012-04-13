# Arc is copyright 2009-2012 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import gzip, os, sys

if len(sys.argv) == 1:
    print "Please provide a filename."
filename = sys.argv[1]
print "Fixing %s..." % filename
gzf = gzip.GzipFile(filename)
ngzf = gzip.GzipFile(filename + ".new", "wb")
ngzf.write(gzf.read(4))
chunk = gzf.read(2048)
while chunk:
    ngzf.write("".join([("\0" if ord(byte) > 49 else byte) for byte in chunk]))
    chunk = gzf.read(2048)
gzf.close()
ngzf.close()
os.rename(filename + ".new", filename)
