# -*- coding: utf-8 -*-
'''
Collect command-line interface (CLI) arguments.
'''
from __future__ import print_function
import sys
from hierosoft import (  # noqa F401
    echo0,
    echo1,
    echo2,
    set_verbosity,
)


class SimpleArgs:

    def __init__(self, title, sequential_keys=None, flags=None,
                 usage_docstring=None, help_dict=None, usage=None,
                 types=None, required=None, defaults=None):
        '''
        Specify the arguments that are accepted or required. Exceptions
        don't need to be caught from this constructor, since they would
        be developer errors and should be corrected before release.
        After running this, run "collect()" and catch errors from there
        and present them to the user as input errors (and call usage()
        to show help in the CLI, or use get_usage() for showing the
        help another way such as in a GUI).

        Sequential arguments:
        title -- Set to None to not prepend a title with equally long
            hyphens as an underline in the usage function.

        Keyword arguments:
        usage -- The usage function to call instead of using title and
            usage_docstring and provided options to generate the rest
            when usage is called. For GUI applications, don't use this.
            Use usage_docstring instead.
        flags -- These arguments do not take a value. For example, one
            the builtin flags of hierosoft are "--verbose" and "--debug"
            and the values are always False unless the flag is present,
            but the next argument is *not* a value--instead, the value
            is always True (In the case of the two builtin flags, they
            also cause a call to set_verbosity(1) and set_verbosity(2)
            respectively). If you need a boolean that the user can set
            to True or False, use the types={key: "bool"} instead
            (not flags). Start with "-" or "--" if applicable. If a key
            has a space, KeyError will be raised.
        help_dict -- Define each argument (start with "--" or "-"
            if applicable). Only arguments in this dict's keys are
            allowed. If None, only ones in types or flags are allowed
            (Otherwise a ValueError is raised). If the key starts with
            "-", the leading hyphens will be stripped before saving the
            value to self.options. If a key has a space, KeyError will
            be raised.
        types -- Use this dict to set the type of a sequential or
            keyword value before saving the value to self.options. If
            the string doesn't cast to the type (such as if "1.1" is
            given for an int), a ValueError is raised by the type's
            constructor. Do not include the leading hyphens.
            If the key starts with "-", or if a key has a space,
            KeyError will be raised. A value in types can either be
            a constructor (including a builtin Python type such as int
            without quotes) or a converter callback function that
            returns the type you want.
        required -- a list of keys that are required. These must *not*
            include the leading "--" and must be keys from either
            types, help_dict, flags, or sequential keys, otherwise the
            keys won't be accepted in the first place and a
            KeyError will be raised (this would be an error on the part
            of the developer not the user). If the user fails to enter
            one or more of the required keys, a ValueError will be
            raised instead. If the key starts with "-", the leading
            hyphens will be stripped before saving the value to
            self.options.
        defaults -- Set all of the return values to this that aren't
            in the user's input (Therefore, defaults must
            already have the correct types otherwise a TypeError is
            raised). Reference types will be set by reference, so if
            the value needs to by a copy, copy it *before* putting it
            in the argument. Also, none of these can start with a
            hyphen or KeyError will be raised (That would be an error on
            the part of the developer, not the user).
        sequential_keys -- These keys are filled in self.options
            whenever an argument appears that isn't preceded by an
            argument that is defined by one of the args (or help_dict
            keys) arguments.

        Raises:
        TypeError -- occurs when the user enters a value that the
            converter can't cast. Other exception types may be raised
            if you use a custom converter function instead of a type in
            types, but in that case if your function always raises a
            TypeError then you can be sure TypeError always has the
            same meaning.
        KeyError -- occurs when the programmer enters incorrect or
            conflicting argument specifications (as arguments to this
            constructor).
        '''
        self.options = None
        if defaults is None:
            defaults = {}
        self.defaults = defaults
        self.title = title
        self._usage = None
        if usage is not None:
            self._usage = usage
        if sequential_keys is None:
            sequential_keys = []
        for key in sequential_keys:
            if key.startswith("-"):
                raise KeyError("Only args or flags can can start with"
                               " '-' not keys, but sequential_keys"
                               " contains '{}'".format(key))
            if len(key.strip()) == 0:
                raise KeyError("There is no key in {}".format(key))
            # Spaces etc in the key: handled further down for all keys.
        if types is None:
            types = {}
        for key, converter in types.items():
            if key.startswith("-"):
                raise KeyError(
                    "{} starts with -: "
                    "The types dictionary must use the finalized"
                    " options key as they dictionary key, not the"
                    " argument (do arg.lstrip('-') on first)."
                    "".format(key)
                )
        if flags is None:
            flags = []
        self.sequential_keys = sequential_keys
        self.flags = flags
        self.usage_docstring = usage_docstring
        if help_dict is None:
            help_dict = {}
        self.help_dict = help_dict

        all_keys = []
        lists = {
            'types': list(types.keys()),
            'sequential_keys': sequential_keys,
            'flags': flags,
            'help_dict': list(help_dict.keys()),
        }
        # ^ lists only exists to track where the error originated.
        #   It can't be a simple reverse lookup, because the key can be
        #   in more than one list.
        for list_name, values in lists.items():
            for arg in values:
                key = arg.lstrip("-")  # only applies to help_dict
                # Others are enforced as having no leading "-" by now.
                all_keys.append(key)
                if len(key) == 0:
                    raise KeyError("There is no key in {} in {}"
                                   "".format(arg, list_name))
                elif " " in key:
                    raise KeyError("The key {} has space(s) in {}"
                                   "".format(arg, list_name))
                elif "\t" in key:
                    raise KeyError("The key {} has tab(s) in {}"
                                   "".format(arg, list_name))
                elif "\n" in key:
                    raise KeyError("The key {} has \\n(s) in {}"
                                   "".format(arg, list_name))
                elif "\r" in key:
                    raise KeyError("The key {} has \\r(s) in {}"
                                   "".format(arg, list_name))

        if required is None:
            required = []
        for arg in required:
            key = arg.lstrip("-")
            if key not in all_keys:
                raise KeyError(
                    " {} has has been required but not defined. It must"
                    " be defined in at least one of: types, help_dict,"
                    " sequential_keys, or flags (This is"
                    " an error on the part of the program using"
                    " Hierosoft SimpleArgs not on the part of"
                    " Hierosoft SimpleArgs itself, nor on the part of"
                    " the user)."
                    "".format(key)
                )
        self.types = types
        self.required = required

    def collect(self):
        '''
        Collect the command-line interface (CLI) arguments as long as
        they are defind (by the constructor arguments). If the
        arguments do not match the programmer's specifications from the
        constructor, an exception will be raised.
        '''
        self.options = {}
        for flag in self.flags:
            self.options[flag] = False
        sequential_count = 0
        key = None
        for i in range(1, len(sys.argv)):
            arg = sys.argv[i]
            if key is not None:
                converter = self.types.get(key)
                if converter is not None:
                    self.options[key] = converter(arg)
                else:
                    self.options[key] = arg
                key = None
            elif arg == "--verbose":
                set_verbosity(1)
            elif arg == "--debug":
                set_verbosity(2)
            elif arg.startswith("--"):
                key = arg[2:]
                if len(key.strip()) < 1:
                    self.usage()
                    raise ValueError(
                        'A blank argument ("{}") was found.'
                        ''.format(arg)
                    )
                if arg in self.flags:
                    self.options[key] = True
                    key = None
                elif self.help_dict is None:
                    # If not in self.flags and None, then no other
                    #   arguments are defined, so arg is incorrect.
                    raise ValueError(
                        '"{}" is an unknown argument.'
                        ''.format(arg)
                    )
                elif arg in self.help_dict.keys():
                    # let the next arg be the value.
                    pass
            elif sequential_count < len(self.sequential_keys):
                # It is assumed to be a value, and the key is assumed
                #   to be the next string defined by
                #   self.sequential_keys.
                key = self.sequential_keys[sequential_count]
                echo1("[hierosoft simpleargs] got sequential value for {}: {}"
                      "".format(key, arg))
                converter = self.types.get(key)
                if converter is not None:
                    # Use the converter at key to convert the arg,
                    #   which is a *value* in this case (since the key
                    #   is already known like in the case of key being
                    #   set but in this case it is known due to order).
                    self.options[key] = converter(arg)
                else:
                    self.options[key] = arg
                del converter
                key = None  # We already know the key by order & used it.
                sequential_count += 1
            else:
                self.usage()
                if len(self.sequential_keys) > 0:
                    raise ValueError(
                        "All of the arguments {} were already set"
                        " but they were followed by an unknown argument: {}"
                        "".format(self.sequential_keys, arg)
                    )
                else:
                    raise ValueError(
                        "There was an unknown argument: {}"
                        "".format(arg)
                    )
        missing = []
        for key in self.required:
            # defaults can't be placed in self.options yet, or this won't work.
            if key not in self.options.keys():
                missing.append(key)
        if len(missing) == 1:
            raise ValueError("{} is required.".format(missing[0]))
        elif len(missing) > 0:
            raise ValueError("These settings are required but missing: {}"
                             "".format(missing))

        for key, value in self.defaults.items():
            if key.startswith("-"):
                raise KeyError(
                    "The key '{}' in defaults cannot start with '-'."
                    " Do arg.lstrip('-') for each argument in defaults."
                    "".format(key)
                )
            converter = self.types.get(key)
            if converter is not None:
                converted = converter(value)
                if value is None:
                    # Allow a default of None.
                    pass
                elif type(value) != type(converted):
                    raise KeyError(
                        # KeyError since that is the programmer error.
                        "The default value {} is a {} but the"
                        " types dictionary specifies {}."
                        "".format(value, type(value).__name__,
                                  type(converted).__name__)
                    )
            if key not in self.options.keys():
                self.options[key] = value

    def get_usage(self):
        if self._usage is not None:
            echo0("Warning: a usage callback is present, but get_usage"
                  " can only generate a multi-line string, so the"
                  " resulting string may differ from the output"
                  " of simpleargs._usage().")
        msg = "\n"
        msg += "\n"
        if self.title is not None:
            msg += self.title + "\n"
            msg += "-" * len(self.title) + "\n"
        if self.usage_docstring is not None:
            msg += self.usage_docstring + "\n"
        else:
            for arg, description in self.help_dict.items():
                type_msg = ""
                key = arg.lstrip("-")
                converter = self.types.get(key)
                if converter is None:
                    converter = self.types.get(arg)
                msg += "{}{} {}".format(key, type_msg, description)
        msg += "\n"
        return msg

    def usage(self):
        if self._usage is not None:
            self._usage()
            return
        echo0(self.get_usage())
