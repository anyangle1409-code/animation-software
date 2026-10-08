"""Necessary statistical consistency checks; passing does not validate anatomy."""
import math
from numbers import Real

def two_group_correlation_upper_bound(n, first_group_n, sample_sd_x,
                                     sample_sd_y, maximum_within_r,
                                     maximum_mean_difference_x,
                                     maximum_mean_difference_y):
 """Conservative necessary bound, conditional on SAME paired observations.

 Sample covariance decomposes into within-group covariance plus
 n1*n2/n * (mean_x1-mean_x2)*(mean_y1-mean_y2). Cauchy-Schwarz bounds
 the within term by max(nonnegative within r) times the TOTAL scatter.
 The between term is bounded by caller-supplied absolute mean differences.
 This deliberately loose bound cannot validate data or estimate a regression.
 """
 if any(isinstance(v,bool) or not isinstance(v,int) for v in [n,first_group_n]) or n<3 or not 0<first_group_n<n:
  raise ValueError('integer sample/group counts with 0 < group n < total n required')
 vals=[sample_sd_x,sample_sd_y,maximum_within_r,maximum_mean_difference_x,maximum_mean_difference_y]
 if not all(isinstance(v,Real) and not isinstance(v,bool) and math.isfinite(v) for v in vals):
  raise ValueError('finite numeric summaries required')
 if sample_sd_x<=0 or sample_sd_y<=0 or not 0<=maximum_within_r<=1 or min(maximum_mean_difference_x,maximum_mean_difference_y)<0:
  raise ValueError('positive SDs, nonnegative mean-difference bounds and within r in [0,1] required')
 weight=(first_group_n/n)*((n-first_group_n)/(n-1))
 between=weight*(maximum_mean_difference_x/sample_sd_x)*(maximum_mean_difference_y/sample_sd_y)
 if not math.isfinite(between):raise ValueError('summary normalization overflow')
 return min(1.,maximum_within_r+between)

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
