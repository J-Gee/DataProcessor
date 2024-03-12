# # Python 3 server example
# from http.server import BaseHTTPRequestHandler, HTTPServer
# import time
#
# hostName = "138.253.125.198"
# serverPort = 80
#
# class MyServer(BaseHTTPRequestHandler):
#     def do_GET(self):
#         self.send_response(200)
#         self.send_header("Content-type", "text/html")
#         self.end_headers()
#         self.wfile.write(bytes("<html><head><title>owo.gov</title></head>", "utf-8"))
#         #self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
#         self.wfile.write(bytes("<body>", "utf-8"))
#         self.wfile.write(bytes("<p>pretty cringe imo</p>", "utf-8"))
#         self.wfile.write(bytes("</body></html>", "utf-8"))
#
# if __name__ == "__main__":
#     webServer = HTTPServer((hostName, serverPort), MyServer)
#     print("Server started http://%s:%s" % (hostName, serverPort))
#
#     try:
#         webServer.serve_forever()
#     except KeyboardInterrupt:
#         pass
#
#     webServer.server_close()
#     print("Server stopped.")


import struct

if struct.calcsize("P") * 8 == 64:

  print("Running in 64-bit mode.")

else:

  print("Not running in 64-bit mode.")