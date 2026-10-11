"""Bounded exact multi-axis box candidates; source coordinates never change."""
from fractions import Fraction
import itertools
import math

from source_triangle_broadphase import _boxes


def candidate_pairs(triangles_a,triangles_b,*,cell_width=1,
                    max_checks=250_000,max_cell_references=500_000,
                    max_cell_pair_visits=2_000_000):
    """Complete closed-box pairs or raise; never return a partial scan.

    Cell width partitions UNVERIFIED source units, not anatomy or a tolerance.
    Floor each closed endpoint exactly; a point in overlapping boxes belongs
    to a cell included by both. Duplicate cell hits are checked once per pair.
    Degenerates/duplicates retain original IDs. Frame compatibility is caller's
    responsibility; box completeness does not mean accepted mesh clearance.
    """
    if (type(cell_width) not in (int,float) or cell_width <= 0 or
            cell_width > 1_000_000 or not math.isfinite(cell_width)):
        raise ValueError('Expected bounded finite positive computational cell width')
    for value,cap in ((max_checks,2_000_000),(max_cell_references,500_000),
                      (max_cell_pair_visits,2_000_000)):
        if type(value) is not int or not 1 <= value <= cap:
            raise ValueError('Expected bounded positive integer work limit')
    width=Fraction(cell_width)
    boxes=[_boxes(triangles_a),_boxes(triangles_b)]
    ranges=[[],[]]
    references=0
    for side in (0,1):
        for lo,hi in boxes[side]:
            bounds=[(lo[k]//width,hi[k]//width) for k in range(3)]
            references+=math.prod(end-start+1 for start,end in bounds)
            if references > max_cell_references:
                raise RuntimeError('Cell reference limit reached; no complete result')
            ranges[side].append(bounds)

    def cells(bounds):
        return itertools.product(*(range(start,end+1) for start,end in bounds))

    grid={}
    for i,bounds in enumerate(ranges[0]):
        for cell in cells(bounds): grid.setdefault(cell,[]).append(i)
    pairs=[]
    checks=0
    visits=0
    for j,bounds in enumerate(ranges[1]):
        seen=set()
        lo,hi=boxes[1][j]
        for cell in cells(bounds):
            for i in grid.get(cell,()):
                visits+=1
                if visits > max_cell_pair_visits:
                    raise RuntimeError('Cell pair-visit limit reached; no complete result')
                if i in seen: continue
                seen.add(i)
                checks+=1
                if checks > max_checks:
                    raise RuntimeError('Candidate comparison limit reached; no complete result')
                other_lo,other_hi=boxes[0][i]
                if all(hi[k] >= other_lo[k] and other_hi[k] >= lo[k] for k in range(3)):
                    pairs.append([i,j])
    return {'triangle_index_pairs':sorted(pairs),'candidate_comparisons':checks,
            'cell_references':references,'cell_pair_visits':visits,
            'source_triangle_counts':[len(boxes[0]),len(boxes[1])],
            'supplied_box_enumeration_complete':True,'whole_surface_clearance_verified':False,
            'anatomical_contact_accepted':False,'physical_units_verified':False}
