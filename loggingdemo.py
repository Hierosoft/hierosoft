"""
See logging-demo.py which imports loggingdemo.
"""
from hierosoft.morelogging import (
    echo0,
    echo1,
)


def foo():
    echo0("Hi")
    echo0()
    echo0("...", stack_trace=False)
    echo1("Bye", multiline=False)


class Bar():
    def __init__(self):
        foo()
