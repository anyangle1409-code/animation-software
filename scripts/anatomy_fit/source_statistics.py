"""Necessary statistical consistency checks; passing does not validate anatomy."""
import math
from numbers import Real

def check_summary(mean, sample_sd, observed_range, n):
 errors=[]
 if isinstance(n,bool) or not isinstance(n,int) or n<2:return ['sample n must be integer >=2']
 if not isinstance(observed_range,(list,tuple)) or len(observed_range)!=2:return ['two observed range bounds required']
 values=[mean,sample_sd,*observed_range]
 if not all(isinstance(x,Real) and not isinstance(x,bool) and math.isfinite(x) for x in values):return ['finite numeric summary required']
 lo,hi=observed_range
 if hi<lo:return ['range reversed']
 if not lo<=mean<=hi:errors.append('mean outside observed range')
 if sample_sd<0:errors.append('negative SD')
 # Popoviciu variance bound with Bessel correction for SAMPLE SD.
 # Conservative with respect to mean and attained for balanced extrema.
 maximum=(hi-lo)/2*math.sqrt(n/(n-1))
 if sample_sd>maximum+0.01:errors.append('SD impossible for bounded sample (0.01 rounding tolerance)')
 return errors
