import http.server
import socket
import threading,sys,queue,time
from evdev import UInput, ecodes as e
from urllib.parse import parse_qsl, urlparse
import qrcode
import ctypes

libc = ctypes.CDLL('libc.so.6')

# win https://stackoverflow.com/questions/62189991/how-to-wrap-the-sendinput-function-to-python-using-ctypes
# lin https://python-evdev.readthedocs.io/en/latest/tutorial.html#injecting-input
# my ip https://stackoverflow.com/a/28950776/824358

PORT = 8080

if len(sys.argv)>1:
	if sys.argv[1].isdigit():
		PORT=int(sys.argv[1])
	else:
		print("Usage: "+sys.argv[0]+" [PORT]")
		print(" Will start listening on the given port. Default port is 8080")
		sys.exit(0)

ui = UInput()
pressed_keys=""
keynames={
"a" : e.KEY_Y,
"b" : e.KEY_U,
"c" : e.KEY_I,
"d" : e.KEY_O,
"e" : e.KEY_P,

"f" : e.KEY_H,
"g" : e.KEY_J,
"h" : e.KEY_K,
"i" : e.KEY_L,
"j" : e.KEY_SEMICOLON,

"k" : e.KEY_N,
"l" : e.KEY_M,
"m" : e.KEY_COMMA,
"n" : e.KEY_DOT,
"o" : e.KEY_SLASH
}

keyqueue=queue.Queue()
tl_start=0
tl_elapsed=0
tr_start=0
tr_elapsed=0
avgping=0

def get_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.settimeout(0)
	IP = '127.0.0.1'
	try:
		# doesn't even have to be reachable
		s.connect(('10.254.254.254', 1))
		IP = s.getsockname()[0]
	except Exception:
		pass
	finally:
		s.close()
	return IP


class WebRequestHandler(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		global pressed_keys,tl_start,tl_elapsed,tr_start,tr_elapsed,avgping,keyqueue
		url=urlparse(self.path)
		if url.path=="/touch.html" or url.path=="/":
			ff=open("touch.html")
			fd=ff.read().encode("utf-8")
			ff.close()
			self.send_response(200)
			self.send_header("Content-Type", "text/html; charset=utf-8")
			self.send_header("Content-Length", str(len(fd)))
			self.send_header("Keep-Alive", "timeout=30, max=300")
			self.end_headers()
			self.wfile.write(fd)
			
		elif url.path=="/send":
			qdata=dict(parse_qsl(url.query))
			tl_now=time.perf_counter()
			if "p" in qdata:
				if int(qdata["p"])==0:
					tl_start=tl_now
					tr_start=int(qdata["t"])*0.001
					avgping=0
					self.send_response(200)
					self.send_header("Content-Length", "0")
					self.send_header("Cache-Control", "no-cache")
					self.send_header("Keep-Alive", "timeout=30, max=300")
					self.end_headers()
					return
				else:
					tl_elapsed=tl_now-tl_start
					tr_elapsed=int(qdata["t"])*0.001-tr_start
					if abs(tl_elapsed-tr_elapsed)>1:
						tl_start=tl_start+(tl_elapsed-tr_elapsed)
						tl_elapsed=tl_now-tl_start
					if avgping==0:
						avgping=int(qdata["p"])
					else:
						avgping=avgping*0.9+int(qdata["p"])*0.1
					print("elapsed: "+str(round(tl_elapsed,3))+"/"+str(round(tr_elapsed,3))+" ("+str(round(tl_elapsed-tr_elapsed,3))+") p="+str(round(avgping)))
			if "k" in qdata:
				presses=qdata["k"].split(';')
			else:
				presses=[]
			for x in presses:
				x2=x.split(',')
				x2.append(tl_now)
				keyqueue.put(x2)
			print ("queue:"+str(keyqueue.qsize()))
			self.send_response(200)
			self.send_header("Content-Length", "0")
			self.send_header("Cache-Control", "no-cache")
			self.send_header("Keep-Alive", "timeout=30, max=300")
			self.end_headers()
		elif url.path=="/favicon.ico":
			self.send_response(404)
			self.send_header("Content-Type", "text/plain; charset=utf-8")
			self.send_header("Content-Length", "0")
			self.send_header("Keep-Alive", "timeout=30, max=300")
			self.end_headers()
		else:
			print("Invalid request: "+self.path)
		
	def do_POST(self):
		self.do_GET()

print("Connect with browser to: http://"+get_ip()+":"+str(PORT)+"/")
qr = qrcode.QRCode()
qr.add_data("http://"+get_ip()+":"+str(PORT)+"/")
qr.print_ascii()

def key_thread():
	global pressed_keys
	while True:
		(keydir,keynum,keytime,instime)=keyqueue.get()
		tl_now=time.perf_counter()
		keydelay=(int(keytime)+avgping/2+30)*0.001-tr_elapsed-(tl_now-instime)
		print("executing key "+str((keydir,keynum,keytime,instime))+" delay "+str(round(keydelay,3))+" after "+str(round(tl_now-instime,3)))
		if keydelay>0:
			libc.usleep(round(keydelay*1000000))
		if keynum in keynames:
			xx=keynames[keynum]
			ui.write(e.EV_KEY, xx, int(keydir))
			if keydir=='1':
				#print(str(round(keydelay,3))+" press "+keynum)
				pressed_keys+=keynum
			else:
				#print(str(round(keydelay,3))+" release "+keynum)
				keypos=pressed_keys.find(keynum)
				if keypos>=0:
					pressed_keys=pressed_keys[:keypos]+pressed_keys[keypos+1:]
			ui.syn()

key_listener=threading.Thread(target=key_thread,daemon=True)
key_listener.start()

with http.server.ThreadingHTTPServer(("", PORT), WebRequestHandler) as httpd:
	print("serving at port", PORT)
	httpd.serve_forever()
