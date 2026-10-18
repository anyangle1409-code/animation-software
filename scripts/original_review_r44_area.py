"""R44 optimizer must use the same area severity ceiling as native validation."""
import numpy as np
def upper_bounds(rest_area,parent_area,parent_max,margin=.009,count_ratio=1.999):
 count_cap=np.where(parent_area<=2*rest_area,np.maximum(count_ratio*rest_area,parent_area),np.inf)
 return np.minimum(count_cap,parent_max[:,None]*(1+margin)*rest_area)
