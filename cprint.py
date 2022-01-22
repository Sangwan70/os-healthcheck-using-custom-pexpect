import datetime
import os
now=datetime.datetime.now()
with_time = now.strftime("%d-%m-%Y %H:%M:%S")
class Colors:
    INFO = "\x1b[36m"
    WARNING = "\x1b[33m"
    ERROR = "\x1b[31m"
    DEFAULT="\x1b[0m"
    END = "\x1b[0m"
    SUCCESS = "\x1b[32m"
    BLINK = "\x1b[5m"
st_err = Colors.ERROR+" [ERROR] "+Colors.END
st_warn = Colors.WARNING+" [WARNING] "+Colors.END
st_info = Colors.INFO+" [INFO] "+Colors.END
st_ok = Colors.SUCCESS + " [SUCCESS] " + Colors.END
default = Colors.DEFAULT +Colors.END

def do_print(message,level=default,dt_time=False):
  if dt_time:
    print(with_time + level + message)
  else:
    print(level + message)

def print_headline(message,width=50,underline=True,colour=Colors.WARNING):
  print('\n'+(Colors.WARNING+ message + Colors.END).center(width))
  if underline:
    print(Colors.WARNING + '-'*width + Colors.END)

def col_print(message,clr):
  print clr+message+Colors.END


