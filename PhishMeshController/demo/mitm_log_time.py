import sys
import re
from datetime import datetime

fileObject = None
try:
    if len(sys.argv) == 2:
        fileObject=open(sys.argv[1],"w")
    for line in sys.stdin:
        # print(line)
        if line.strip() != "":
            if re.match("^(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]*", line.strip()):
                line = "\n[MITM_LOG @ "+datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + "] :: " + line
                # print(line)

            if fileObject:
                fileObject.write(line)
                fileObject.flush()

except:
    if fileObject:
        fileObject.close()
    
