import os
import glob
import sys
sys.path.insert(0, '..')
import settings
import util

root = util.relpath(__file__, '..')
folder = os.path.join(root, settings.PROFILER_OUTPUT_ROOT, )
for filename in glob.glob(folder + '/*.profile_out'):
    print filename
    base, ext = os.path.splitext(filename)
    #print base
    #print ext
    graph_filename = base + '.png'
    #print graph_filename
    if not os.path.exists(graph_filename):
        print '  Creating graph...'
        os.system('gprof2dot.py -f pstats %s | dot -Tpng -o %s' % (filename, graph_filename))
