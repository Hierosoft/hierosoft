"""
See logging-demo.py which imports loggingdemo.
"""
from hierosoft.morelogging import (
    echo0,
    echo1,
    write0,
    write1,
)


def foo():
    echo0("Hi")
    echo0()
    echo0("...", stack_trace=False)
    write0("On one line...")
    echo0("OK")
    write1("On one line...")
    echo1("OK")
    echo1("Bye", multiline=False)


class Bar():
    def __init__(self):
        foo()
