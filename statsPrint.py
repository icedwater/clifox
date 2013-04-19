import sys,pstats
if len(sys.argv)<2:
 print "stats printer"
 print "run as:"
 print "python %s statsFile [-1|count] [sortKey]" % (sys.argv[0],)
 print "where count is the top n calls to list"
 print "where statsFile is the file generated from doing \"python -mcProfile -o stats_filename_here ./clifox\""
 print "where sortKey is cumulative, time or other (refer to cProfile docs)"
 sys.exit(0)
s=pstats.Stats(sys.argv[1])
try:
 num=sys.argv[2]
 if num in ["*","","-1"]:
  s.sort_stats("cumulative" if len(sys.argv)<3 else sys.argv[2]).print_stats()
 else:
  s.sort_stats("cumulative").print_stats(num)
except:
  s.sort_stats("cumulative").print_stats(100)

