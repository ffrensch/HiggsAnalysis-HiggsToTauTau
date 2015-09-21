#!/usr/bin/env python
import itertools
import HiggsAnalysis.HiggsToTauTau.combine.utils as utils
from HiggsAnalysis.HiggsToTauTau.combine.opts import OPTS

from HiggsAnalysis.HiggsToTauTau.combine.base import CombineToolBase

class EnhancedCombine(CombineToolBase):
  description = 'Just passes options through to combine with special treatment for a few args'
  requires_root = False
  def __init__(self):
    CombineToolBase.__init__(self)

  def attach_intercept_args(self, group):
    CombineToolBase.attach_intercept_args(self, group)
    group.add_argument('-m', '--mass')
    group.add_argument('--points')
    group.add_argument('--name', '-n', default='Test')

  def attach_args(self, group):
    CombineToolBase.attach_args(self, group)
    group.add_argument('--opts', nargs='+', default=[], help='Add preset combine option groups')
    group.add_argument('--coalesce', '-c', type=int, default=1, help='comine this many jobs')
    group.add_argument('--split-points', type=int, default=0, help='If > 0 splits --algo grid jobs')
  
  def set_args(self, known, unknown):
    CombineToolBase.set_args(self, known, unknown)
    if hasattr(self.args, 'opts'):
      for opt in self.args.opts:
        self.passthru.append(OPTS[opt])

  def run_method(self):
    ## Put the method back in because we always take it out
    self.put_back_arg('method', '-M')
    self.put_back_arg('name', '-n')

    cmd_queue = []
    subbed_vars = {}

    if self.args.mass is not None:
      mass_vals = utils.split_vals(self.args.mass)
      subbed_vars[('MASS',)] = [(mval,) for mval in mass_vals]
      self.passthru.extend(['-m', '%(MASS)s'])

    if self.args.points is not None: self.passthru.extend(['--points', self.args.points])
    if (self.args.split_points is not None and
        self.args.split_points > 0 and
        self.args.points is not None):
      points = int(self.args.points)
      split = self.args.split_points
      start = 0
      ranges = [ ]
      while (start + (split-1)) <= points:
        ranges.append((start, start + (split-1)))
        start += split
      if start < points:
        ranges.append((start, points - 1))
      subbed_vars[('P_START', 'P_END')] = [(r[0], r[1]) for r in ranges]
      self.passthru.extend(['--firstPoint %(P_START)s --lastPoint %(P_END)s', '-n', '.POINTS.%(P_START)s.%(P_END)s'])

    proto = 'combine '+(' '.join(self.passthru))
    for it in itertools.product(*subbed_vars.values()):
      keys = subbed_vars.keys()
      dict = {}
      for i, k in enumerate(keys):
        for tuple_i, tuple_ele in enumerate(k):
          dict[tuple_ele] = it[i][tuple_i]
      self.job_queue.append(proto % dict)
    self.flush_queue()


