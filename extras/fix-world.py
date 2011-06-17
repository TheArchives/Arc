

import gzip, sys, os

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
os.rename(filename+".new", filename)
