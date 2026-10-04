import sys
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
beta = sys.argv[1]
exec(open(SP + r"\wing_screen.py").read().split("final = [i for i")[0])
Wm = modify(float(beta))
ids = np.array(sorted(set(left.tolist()) | set(right.tolist())))
np.savez(SP + r"\wing_sol_b%s.npz" % beta, vertices=ids, bones=np.array(bones), weights=Wm[ids])
print("solution b%s: %d vertices, max |dW| %.3f" % (beta, len(ids), abs(Wm[ids] - W[ids]).max()))
