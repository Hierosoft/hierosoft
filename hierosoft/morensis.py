# -*- coding: utf-8 -*-
'''
morensis
by Jake Gustafson

Project: hierosoft Python module by Hierosoft
'''

from collections import OrderedDict


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
        with open(self.path, 'r') as stream:
            for rawL in stream:
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
                    raise SyntaxError('{}, line {}: {}'.format(
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
                if (type_name == 'date') or isinstance(value, str):
                    # Save it with quotes.
                    encoded = '"{}"'.format(value)
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
