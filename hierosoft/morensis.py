# -*- coding: utf-8 -*-
'''
morensis
by Jake Gustafson

Project: hierosoft Python module by Hierosoft
'''
import os
import shutil
import tempfile

from collections import OrderedDict

from hierosoft import (
    echo0,
)


def python_encoded(value):
    if isinstance(value, str):
        return '"{}"'.format(value.replace('"', '\\"'))
    return str(value)


def rewrite_python_var(path, key, value):
    """Rewrite a Python file and change a value.

    Args:
        value: If the value is a str, quotes will be added.
    """
    prevLineN = None
    lineN = 0
    if not key:
        raise ValueError('No variable name was set (got {}).'.format(key))
    if key[0].isdigit():
        raise ValueError('A Python variable name must not start with a digit.')
    bads = "\\\n\r\t;:@#$%^&*!?-(){}[]<>`~\"' "
    # ^ Do not allow characters that are not allowed in Python symbols
    #   (but "." is allowed since it may be setting an object attribute)
    for bad in bads:
        if bad in key:
            raise ValueError(
                'The variable name must not contain "{}"'
                ''.format(bad)
            )
    openers = []
    enders = "\t ="
    with tempfile.TemporaryDirectory() as tmpdirname:
        print('created temporary directory', tmpdirname)
        # temp_dir.name
        tmpPath = os.path.join(tmpdirname, path)
        with open(tmpPath, 'w') as ostream:
            with open(path, 'r') as istream:
                for rawL in istream:
                    lineN += 1
                    indented = rawL.rstrip(rawL)
                    line = indented.strip()
                    indent = indented[len(indented)-len(line):]
                    if (line.startswith(key)
                            and (line[len(key):len(key)+1] in enders)):
                        if prevLineN:
                            echo0('File "{}", line {}: Warning:'
                                  ' already had {} on line {}'
                                  ''.format(path, lineN, key, prevLineN))
                        prevLineN = lineN
                        encoded = python_encoded(value)
                        ostream.write(indent+"{} = {}\n"
                                      "".format(key, encoded))
                    else:
                        if line == key:
                            echo0('File "{}", line {}: Warning:'
                                  ' {} has no value, so left untouched'
                                  ''.format(path, lineN, key))
                        ostream.write(rawL)
            if prevLineN is None:
                echo0('File "{}", line {}: Warning:'
                      ' {} was not found, so it will be added to the end!'
                      ''.format(path, lineN, key))
                ostream.write("\n{} = {}\n".format(key, value))
                        
        shutil.move(tmpPath, path)


class NSISInclude:
    """Load and process NSIS Setup include files.
    The files can only contain blank lines, comments, and !define
    statements, otherwise they will not be processed correctly.

    Attributes:
        _pre_var_comments (list[str]): comments and blank lines that
            appear before a given variable in vars.
        _post_comments (list[str]): comments and blank lines at end of
            file.
        path (str): The path of the file that was loaded (set it
            manually before save if no file was loaded).
        vars (OrderedDict): All of the !define names and values.
    """
    def __init__(self):
        self.path = None
        self.vars = OrderedDict()
        self._post_comments = []
        self._pre_var_comments = OrderedDict()
        self.types = {}

    def load(self, path):
        """Load an NSIS include file.
        It must only have blank lines, comments, and !define statements.

        Args:
            path (str): The NSIS file path.
        """
        if not path:
            raise ValueError("No file was specified.")
        self.path = path
        self._post_comments = []
        self._pre_var_comments = OrderedDict()
        self.types = {}
        plain_openers = ["!define /date", "!define"]
        # ^ Starts with larger when overlaps to avoid misidentification
        openers = []
        for opener in plain_openers:
            openers.append(opener+" ")
            openers.append(opener+"\t")
        lineN = 0
        with open(self.path, 'r') as stream:
            for rawL in stream:
                lineN += 1  # Counting numbers start at 1.
                line = rawL.strip()
                if not line:  # blank
                    self._post_comments.append(rawL.rstrip("\r\n"))
                    continue
                if line.startswith(";"):
                    self._post_comments.append(rawL.rstrip("\r\n"))
                    # ^ moved to _pre_var_comments if followed by var
                    continue
                opener = None
                for i in range(len(openers)):
                    if line.startswith(openers[i]):
                        opener = openers[i]
                        break
                if not opener:
                    raise SyntaxError('File "{}", line {}: {}'.format(
                        self.path,
                        lineN,
                        ("Can only process include if all lines start with"
                         " {} or ';' (comment)".format(plain_openers)),
                    ))
                assignment = line[len(opener):].strip()
                spaceI = assignment.find(" ")
                tabI = assignment.find("\t")
                if (spaceI < 0):
                    spaceI = tabI
                elif (tabI > -1) and (tabI < spaceI):
                    # Tab exists and is before space, so end name there.
                    spaceI = tabI
                if spaceI < 0:
                    name = assignment
                    value = ""
                else:
                    name = assignment[:spaceI].strip()
                    value = assignment[spaceI:].strip()
                if ((len(value) >= 2) and value.startswith('"')
                        and value.endswith('"')):
                    value = value[1:-1]
                    if "/date" in opener:
                        self.types[name] = 'date'
                else:
                    # If there are no quotes, assume integer
                    #   unless has dot:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                self.vars[name] = value
                if len(self._post_comments) > 0:
                    self._pre_var_comments[name] = self._post_comments
                    self._post_comments = []

    def save(self):
        """Save the file to path in NSIS format.
        """
        if self.path is None:
            raise ValueError('Load or set path first.')
        for key, value in self.vars.items():
            if ((" " in key) or ("\t" in key) or ("\n" in key)
                    or ("\r" in key)):
                raise KeyError(
                    'Variable names must not contain spaces but got "{}"'
                    ''.format(key)
                )
        with open(self.path, 'w') as stream:
            for key, value in self.vars.items():
                comments = self._pre_var_comments.get(key)
                if comments:
                    for comment in comments:
                        stream.write(comment)
                encoded = value
                type_name = self.types.get(key)
                if value is None:
                    encoded = ""  # No quotes or anything, just blank
                elif (type_name == 'date') or isinstance(value, str):
                    # Save it with quotes.
                    encoded = '"{}"'.format(value.replace('"', '\\"'))
                if type_name:
                    stream.write("!define /{} {} {}\n"
                                 "".format(type_name, key, encoded))
                else:
                    stream.write("!define {} {}\n".format(key, encoded))
            if self._post_comments:
                for comment in self._post_comments:
                    stream.write(comment)

    def get(self, key):
        got = self.vars.get(key)
        if isinstance(got, int):
            echo0('Warning: {} is an int, but get was used'
                  ' (expected get_int). Returning str not int.'
                  ''.format(key))
            return str(got)
        return got

    def get_int(self, key):
        got = self.vars.get(key)
        if not isinstance(got, int):
            echo0('Warning: {} is not an int, but get_int was used'
                  ' (expected get). Returning int anyway.'
                  ''.format(key))
        if got is None:
            return None
        return int(got)

    def set(self, key, value):
        self.vars[key] = value

    def set_int(self, key, value):
        self.vars[key] = int(value)
