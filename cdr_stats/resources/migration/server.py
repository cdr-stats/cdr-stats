import SimpleHTTPServer
import SocketServer

PORT = 8000

class MyHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def guess_type(*args,**kwargs):
        #print args , kwargs
        res = SimpleHTTPServer.SimpleHTTPRequestHandler.guess_type(*args,**kwargs)
        print res
        return res

Handler = MyHTTPRequestHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()