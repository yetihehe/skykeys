import http.server
import socket
import sys,os,queue,time
import threading
import ctypes as ct
import ctypes.wintypes as w
from urllib.parse import parse_qsl, urlparse
import qrcode

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

pressed_keys=""
keynames={
"a" : 0x15, # y
"b" : 0x16, # u
"c" : 0x17, # i
"d" : 0x18, # o
"e" : 0x19, # p

"f" : 0x23, # h
"g" : 0x24, # j
"h" : 0x25, # k
"i" : 0x26, # l
"j" : 0x27, # ;

"k" : 0x31, # n
"l" : 0x32, # m
"m" : 0x33, # ,
"n" : 0x34, # .
"o" : 0x35 # /
}

keyqueue=queue.Queue()
tl_start=0
tl_elapsed=0
tr_start=0
tr_elapsed=0
avgping=0

KEYEVENTF_SCANCODE = 0x8
KEYEVENTF_UNICODE = 0x4
KEYEVENTF_KEYUP = 0x2
INPUT_KEYBOARD = 1

# not defined by wintypes
ULONG_PTR = ct.c_size_t

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

class KEYBDINPUT(ct.Structure):
		_fields_ = [('wVk' , w.WORD),
								('wScan', w.WORD),
								('dwFlags', w.DWORD),
								('time', w.DWORD),
								('dwExtraInfo', ULONG_PTR)]

class MOUSEINPUT(ct.Structure):
		_fields_ = [('dx' , w.LONG),
								('dy', w.LONG),
								('mouseData', w.DWORD),
								('dwFlags', w.DWORD),
								('time', w.DWORD),
								('dwExtraInfo', ULONG_PTR)]

class HARDWAREINPUT(ct.Structure):
		_fields_ = [('uMsg' , w.DWORD),
								('wParamL', w.WORD),
								('wParamH', w.WORD)]

class DUMMYUNIONNAME(ct.Union):
		_fields_ = [('mi', MOUSEINPUT),
								('ki', KEYBDINPUT),
								('hi', HARDWAREINPUT)]

class INPUT(ct.Structure):
		_anonymous_ = ['u']
		_fields_ = [('type', w.DWORD),
								('u', DUMMYUNIONNAME)]

def zerocheck(result, func, args):
		if result == 0:
				raise ct.WinError(ct.get_last_error())
		return result

user32 = ct.WinDLL('user32', use_last_error=True)
SendInput = user32.SendInput
SendInput.argtypes = w.UINT, ct.POINTER(INPUT), ct.c_int
SendInput.restype = w.UINT
SendInput.errcheck = zerocheck

def send_scancode(code, key_down):
		i = INPUT()
		i.type = INPUT_KEYBOARD
		i.ki = KEYBDINPUT(0, code, KEYEVENTF_SCANCODE, 0, 0)
		if not key_down:
			i.ki.dwFlags |= KEYEVENTF_KEYUP
		ret=SendInput(1, ct.byref(i), ct.sizeof(INPUT))
		print("sendinput: "+str(ret))

class WebRequestHandler(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		global pressed_keys,tl_start,tl_elapsed,tr_start,tr_elapsed,avgping,keyqueue
		url=urlparse(self.path)
		#filematch=re.fullmatch("/[^/\\]+",url.path)
		if url.path=="/touch.html" or url.path=="/":
			ff=open("touch.html")
			fd=ff.read().encode()
			ff.close()
			self.send_response(200)
			self.send_header("Content-Type", "text/html; charset=utf-8")
			self.send_header("Content-Length", str(len(fd)))
			self.send_header("Keep-Alive", "timeout=30, max=300")
			self.end_headers()
			self.wfile.write(fd)
		# elif filematch:
			# ff=open(url.path[1:])
			# fd=ff.read().encode("utf-8")
			# ff.close()
			# self.send_response(200)
			# self.send_header("Content-Type", "application/octet-stream; charset=utf-8")
			# self.send_header("Content-Length", str(len(fd)))
			# self.send_header("Keep-Alive", "timeout=30, max=300")
			# self.end_headers()
			# self.wfile.write(fd)
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
		else:
			self.send_response(404)
			self.send_header("Content-Type", "text/plain; charset=utf-8")
			self.send_header("Content-Length", "0")
			self.send_header("Keep-Alive", "timeout=30, max=300")
			self.end_headers()
		
	def do_POST(self):
		self.do_GET()

def key_thread():
	global pressed_keys
	while True:
		(keydir,keynum,keytime,instime)=keyqueue.get()
		tl_now=time.perf_counter()
		keydelay=(int(keytime)+avgping/2+30)*0.001-tr_elapsed-(tl_now-instime)
		print("executing key "+str((keydir,keynum,keytime,instime))+" delay "+str(round(keydelay,3))+" after "+str(round(tl_now-instime,3)))
		if keydelay>0:
			time.sleep(keydelay)
		if keynum in keynames:
			xx=keynames[keynum]
			if keydir=='1':
				send_scancode(xx, True)
				print(str(round(keydelay,3))+" press "+keynum)
				pressed_keys+=keynum
			else:
				send_scancode(xx, False)
				print(str(round(keydelay,3))+" release "+keynum)
				keypos=pressed_keys.find(keynum)
				if keypos>=0:
					pressed_keys=pressed_keys[:keypos]+pressed_keys[keypos+1:]

key_listener=threading.Thread(target=key_thread,daemon=True)
key_listener.start()

print("Connect with browser to: http://"+get_ip()+":"+str(PORT)+"/")
qr = qrcode.QRCode()
qr.add_data("http://"+get_ip()+":"+str(PORT)+"/")
qr.print_ascii()

with http.server.ThreadingHTTPServer(("", PORT), WebRequestHandler) as httpd:
	print("serving at port", PORT)
	httpd.serve_forever()
