"""
See logging-demo.py which imports loggingdemo.
"""
from hierosoft.morelogging import (
    echo0,
    echo1,
)


def foo():
    echo0("Hi")
    echo1("Bye")


class Bar():
    def __init__(self):
        foo()
