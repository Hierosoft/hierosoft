# Training Disclosure for hierosoft-logistics
This Training Disclosure, which may be more specifically titled above here (and in this document possibly referred to as "this disclosure"), is based on **Training Disclosure version 1.1.4** at https://github.com/Hierosoft/training-disclosure by Jake Gustafson. Jake Gustafson is probably *not* an author of the project unless listed as a project author, nor necessarily the disclosure editor(s) of this copy of the disclosure unless this copy is the original which among other places I, Jake Gustafson, state IANAL. The original disclosure is released under the [CC0](https://creativecommons.org/public-domain/cc0/) license, but regarding any text that differs from the original:

This disclosure also functions as a claim of copyright to the scope described in the paragraph below since potentially in some jurisdictions output not of direct human origin, by certain means of generation at least, may not be copyrightable (again, IANAL):

Various author(s) may make claims of authorship to content in the project not mentioned in this disclosure, which this disclosure by way of omission unless stated elsewhere implies is of direct human origin unless stated elsewhere. Such statements elsewhere are present and complete if applicable to the best of the disclosure editor(s) ability. Additionally, the project author(s) hereby claim copyright and claim direct human origin to any and all content in the subsections of this disclosure itself, where scope is defined to the best of the ability of the disclosure editor(s), including the subsection names themselves, unless where stated, and unless implied such as by context, being copyrighted or trademarked elsewhere, or other means of statement or implication according to law in applicable jurisdiction(s).

Disclosure editor(s): Hierosoft LLC

Project author: Hierosoft LLC

This disclosure is a voluntary of how and where content in or used by this project was produced by LLM(s) or any tools that are "trained" in any way.

The main section of this disclosure lists such tools. For each, the version, install location, and a scope of their training sources in a way that is specific as possible.

Subsections of this disclosure contain prompts used to generate content, in a way that is complete to the best ability of the disclosure editor(s).

tool(s) used:
- GPT-4-Turbo (Version 4o, chatgpt.com)

Scope of use: code described in subsections--typically modified by hand to improve logic, variable naming, integration, etc.

## hierosoft
### morelogging
- 2025-01-24

get the name of each function or module in the stack and set callstack_str to ".".join(names) in Python.

My function is now ```
def echo0(*args, **kwargs):  # formerly prerr
    """Show the message and where in the program we are
    Like print_debug from Godot except callstack on same line
    """
    # This level is like logging.CRITICAL
    # logging.CRITICAL = 50
    start = 1  # only skip self (keep caller)
    stack = inspect.stack()
    current_frame = inspect.currentframe()
    # call_frame = inspect.getouterframes(current_frame, 2)
    stack_str = ""
    prefix = ""
    if len(stack) >= start + 1:
        # for i in range(1, len(call_frame)):
        # [3] is caller_name (but works with older Python)
        # module = inspect.getmodule(call_frame[i]) # always "inspect"...
        # name = call_frame[i][3]
        # if not isinstance(name, str):
        # if module and hasattr(module, '__name__'):
        #     # name = name.__name__
        #     name = module.__name__
        # stack_str = name + " " + stack_str
        names = [frame.function for frame in stack[1:]]
        prefix = "[{}] ".format(".".join(reversed(names)))
        if not args:
            args = [prefix]
        else:
            if prefix not in args[0]:
                args = list(args)  # since tuple doesn't support item assignment
                args[0] = prefix + args[0]
                args = tuple(args)
    # Python 2 (without print_function) print >> sys.stderr, args
    kwargs['file'] = sys.stderr  # this way prevents dup named arg in print
    print(*args, **kwargs)
    return True ``` and it is in a submodule called hierosoft.morelogging. the program using it is ```from hierosoft.morelogging import echo0

# For most purposes, use logging2, but to see
#   the callstack, continue to use echo0
#   which has been enhanced to show the
#   callstack. This program should show:
# "[logging-demo.Bar.__init__.foo] Hi"


def foo():
    echo0("Hi")


class Bar():
    def __init__(self):
        foo()


bar = Bar()``` However, it prints "[<module>.__init__.foo] Hi" but I want to know the name of whatever is the parent of __init__ not just say "<module>"

To test this better, I made a client module named "loggingdemo.py": 
```from hierosoft.morelogging import echo0

# For most purposes, use logging2, but to see
#   the callstack, continue to use echo0
#   which has been enhanced to show the
#   callstack. This program should show:
# "[logging-demo.Bar.__init__.foo] Hi"


def foo():
    echo0("Hi")


class Bar():
    def __init__(self):
        foo()
 and the program is now just: 
from loggingdemo import Bar


bar = Bar()
```. It has the information, but it isn't organized. You are putting the module name before everything instead of prepending it to names before the bottom (__main__ in this case). Therefore I get the following output from the main script: "[__main__.<module> loggingdemo.__init__ loggingdemo.foo] Hi" but I am trying to get something more clear like "[__main__ loggingdemo.__init__.foo] Hi"

Why isn't class Bar included? How can we get that? I would expect loggingdemo.__init__.foo to be loggingdemo.Bar.__init__.foo

frame tuple has no attribute function in python 2. Which item in the tuple is the function?

For backward compatibility use .format instead of string interpolation
