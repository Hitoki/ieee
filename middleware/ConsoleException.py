
class ConsoleExceptionMiddleware:
    def process_exception(self, request, exception):
        #print 'process_exception()'
        import traceback
        import sys
        exc_info = sys.exc_info()
        print "\n######################## Exception #############################"
        print '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        print "################################################################"
        #print repr(request)
        #print "################################################################"
