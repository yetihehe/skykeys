# SkyKeys

## Description
This tool allows you to play instruments on PC version of Sky: Children of the Light using touch inteface like mobile phone version. You need to run skykeys_win.exe on your PC, open provided url on a mobile phone and
all keys pressed on mobile phone will be sent to your PC as keypresses. Requirement: PC and phone needs to be in the same network (preferably connected to the same wifi).

## Installation

Windows:

Download skykeys_win.exe and touch.html (conveniently packed in skykeys_win.zip), place them in the same folder and run the program. It should open a window with URL and a helpful QR code. Enter url or scan QR code on mobile phone and open page.
Rectangles pressed on phone will be transferred as keypresses to PC, this can be verified in any program supporting text input (such as notepad). When Sky is in focus, keys will be sent to sky. Open any instrument and play.

Linux:

Install python3 and python-evdev package. Download skykeys_lin.py and touch.html. Run `python3 skykeys_lin.py` in terminal. It should output URL and a helpful QR code. Enter url or scan QR code on mobile phone and open page.
Rectangles pressed on phone will be transferred as keypresses to PC, this can be verified in any program supporting text input (such as notepad). When Sky is in focus, keys will be sent to sky. Open any instrument and play.

## Usage

Both versions allow changing listening port by giving it as first argument to program:

Windows:

```
skykeys_win.exe 8083
```

Linux:
```
python3 skykeys_lin.py 8083
```

## Support

If you can't open page on mobile phone, check if you are on wifi and in the same network as PC, if your firewall is disabled or add a special rule for inbound traffic to this program.

If you see page and it looks like it works, but keypresses are not timed properly or missing, check if your wifi is not congested. Under keyboard there should be list of last sent key codes with ping time. That time should be below 50ms. 25ms is typical.

## Contributing

Send me a message or pull request if you want to make this program better.

## Roadmap

I want to add support for backgrounds and scaling keyboard and keys size with a slider. Some nice icons for keys and maybe animations would be handy too.

## License
This project is available as public domain. You can do anything you want with it, just don't sue me when you publish your version under your name.
