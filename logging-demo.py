from loggingdemo import Bar


# For most purposes, use logging2, but to see
#   the callstack, continue to use echo0
#   which has been enhanced to show the
#   callstack. This program should show:
#   "[__main__ loggingdemo.__init__ foo] Hi"
#   (__main__ refers to this script).

bar = Bar()
