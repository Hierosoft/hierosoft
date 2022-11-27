# -*- coding: utf-8 -*-

class SimpleArgs:

    def __init__(self, title, sequential_keys=None, boolean_keys=None,
                 usage_docstring=None, help_dict=None, usage=None,):
        '''
        Sequential arguments:
        title -- Set to None to not prepend a title with equally long
            hyphens as an underline in the usage function.

        Keyword arguments:
        usage -- The usage function to call instead of using title and
            usage_docstring and provided options to generate the rest
            when usage is called.
        '''
        self.title = title
        self._usage = None
        if usage is not None:
            self._usage = usage
        self.options = {}
        if sequential_keys is None:
            sequential_keys = []
        if boolean_keys is None:
            boolean_keys = []
        self.sequential_keys = sequential_keys
        self.boolean_keys = boolean_keys
        self.usage_docstring = usage_docstring
        self.help_dict = help_dict

        key = None
        for i in range(len(sys.argv)):
            arg = sys.argv[i]
            if key is not None:
                self.options[key] = arg
                key = None
            elif arg.startswith("--verbose"):
                set_verbosity(1)
            elif arg.startswith("--debug"):
                set_verbosity(2)
            elif arg.startswith("--"):
                key = arg[2:]
                if len(key) < 1:
                    self.usage()
                    raise ValueError('A blank argument ("--") was found.")
                if key in boolean_keys:
                    self.options[key] = True
                    key = None
                # else let the next arg be the value.
            elif arg in sequential_keys:
                key = None
                for key_i in range(len(sequential_keys)):
                    try_key = sequential_keys[key_i]
                    if self.options.get(try_key) is None:
                        key = try_key
                        break
                if key is None:
                    self.usage()
                    if len(sequential_keys) > 0:
                        raise ValueError(
                            "All of the arguments {} were already set"
                            " but they were followed by an unknown argument: {}"
                            "".format(sequential_keys, arg)
                        )
                    else:
                        raise ValueError(
                            "There was an unknown argument: {}"
                            "".format(sequential_keys)
                        )
                self.options[key] = arg
                key = None  # We already know the key by order & used it.

    def get_usage()
        if self._usage is not None:
            echo0("Warning: a usage callback is present, but get_usage"
                  " can only generate a multi-line string, so the"
                  " resulting string may differ from the output"
                  " of simpleargs._usage().")
        msg = "\n"
        msg += "\n"
        if self.title is not None:
            msg += title + "\n"
            msg += "-" * len(title) + "\n"
        if self.usage_docstring is not None:
            msg += self.usage_docstring + "\n"
        msg += "\n"

    def usage():
        if self._usage is not None:
            self._usage()
            return
        echo0(self.get_usage())
