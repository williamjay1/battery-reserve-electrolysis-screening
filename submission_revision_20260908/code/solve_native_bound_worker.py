from pathlib import Path
import sys,json
import numpy as np
from native_hydrogen_bound import upper_bound
a=np.load(sys.argv[1],mmap_mode='r')
E=float(sys.argv[2]);S=float(sys.argv[3]);target=Path(sys.argv[4])
upper,iterations=upper_bound(a,E,.75,S,K=17)
target.write_text(json.dumps(dict(upper_mwh=upper,iterations=iterations)))
