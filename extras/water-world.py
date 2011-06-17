

import gzip, sys, os

if len(sys.argv) == 1:
    print "Please provide a filename."
filename = sys.argv[1]
print "Converting still water to normal water in %s..." % filename
gzf = gzip.GzipFile(filename)
ngzf = gzip.GzipFile(filename + ".new", "wb")
ngzf.write(gzf.read(4))
chunk = gzf.read(2048)
while chunk:
    ngzf.write("".join([("\8" if ord(byte) == 9 else byte) for byte in chunk]))
    chunk = gzf.read(2048)
gzf.close()
ngzf.close()
os.rename(filename+".new", filename)
