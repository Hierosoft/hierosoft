def property_to_kv_value(property):
    '''
    Change a real Python type value to a KV-encoded value,
    adding quotes if StringProperty or string.
    NOTE: id should *not* have quotes, so convert id using
    str(property) (or implicit conversion to str) *not* this function.
    '''
    if property is None:
        return None
    if ((type(property).__name__ == "ReferenceListProperty")
            or (type(property).__name__ == "ObservableList")
            or (type(property).__name__ == "ObservableReferenceList")
            or (type(property).__name__ == "tuple")
            or (type(property).__name__ == "list")):
        count = 0
        parts = []
        for sub_property in property:
            sub_value = property_to_kv_value(sub_property)
            parts.append(sub_value)
            if sub_value is not None:
                count += 1
        if count == 0:
            return None
        return str(parts)[1:-1]  # 1:-1 to remove braces
        # ^ Change "[1.0, None]" to "1.0, None" for use in KV
    if ((type(property).__name__ == "StringProperty")
            or (type(property).__name__ == "str")):
        return "'{}'".format(property.replace("'", "\\'"))
    if type(property).__name__ == "dp":
        return "{}dp".format(float(property))
    if ((type(property).__name__ == "ObjectProperty")
            or (type(property).__name__ == "dict")):
        # Example: "pos_hint is an ObjectProperty containing a dict."
        try:
            if len(property.keys()) == 0:
                # Such as pos_hint with no settings
                return None
            count = 0
            for value in property.values():
                if value is not None:
                    count += 1
            if count < 1:
                return None
        except AttributeError:
            # ObjectProperty of unknown type should
            #   silently degrade to str() or implicit
            #   conversion below.
            pass
    if type(property).__name__ in ["float", "int", "bool", "dict"]:
        # for string, see "str" case further up.
        return str(property)
    raise NotImplementedError("type: {}".format(type(property).__name__))
    return str(property)
    # ^ else Python-like dict representation is ok for pos_hint in kvlang
    #   (See <https://stackoverflow.com/a/45100701/4541104>).


_id_lookup = {}  # Look up the id of a widget.


def set_widget_id(widget, widget_id):
    '''
    Collect the Kivy id of the widget to add it to the lookup table so
    that later calls to get_widget_id can provide the kivy id.

    Internally, this method uses the _id_lookup global dictionary,
    where the key is the Python id and the value is the Kivy id.
    '''
    if widget_id is None:
        raise ValueError(
            "set_widget_id must only be used with non-None widget_id"
        )
    _id_lookup[str(id(widget))] = widget_id


def get_widget_id(widget):
    '''
    Get the Kivy id of the widget (only works if either the widget has
    an id set *or* the id was recorded using set_widget_id, in which
    case this module's own reflection feature will be used to determine
    the id.

    Internally, this method uses the _id_lookup global dictionary,
    where the key is the Python id and the value is the Kivy id.
    '''
    if hasattr(widget, 'id'):
        if (widget.id is not None) and (widget.id != ""):
            return widget.id
    return _id_lookup.get(str(id(widget)))


def widget_to_kv(widget, indent, widget_id=None, outfn=print,
                 className=None):
    """Show information about one widget, for debugging purposes.

    This method is designed to translate Python-generated
    widgets into KV (kvlang code).

    The resulting KV shown on the console can
    be used with https://github.com/kivymd/KivyMDBuilder, then
    the resulting KV can be translated back into the Python
    calls of the given ids (managed by SinglePage instances in
    this App).

    Args:
        widget_id (str): Specify a dictionary key or variable name in
            (from the App) which is used to access this
            widget. This will be used as the "id" in the KV file.
            Otherwise, id will be ignored (since this method assumes
            that the widgets were dynamically generated in a py
            file rather than a kv file which has ids)
        outfn (Callable): The output function (print to console by
            default); The given function itself must add a newline at
            the end like print does.
        className (str): You must set this if you are using a widget subclass
            so that the KV language output is written properly. For
            example, if you have a "SinglePage" class that is a
            subclass of KivyMD's "MD3Card", you must set className to
            "<SinglePage@MD3Card>" (including the "<>" signs).
    """
    if widget is None:
        outfn(indent + "# None")
        if widget_id is not None:
            outfn(indent + "#     id: {}".format(widget_id))
        return False
    if className is None:
        className = type(widget).__name__
    outfn(indent + className + ":")
    child_indent = indent + "    "
    echo_any = False
    if widget_id is not None:
        outfn(child_indent + "id: {}".format(widget_id))
        # ^ id must be converted using str()
        #   (or implicit conversion to str)
        #   *not* property_to_kv_value,
        #   because id doesn't have quotes in kvlang.
        echo_any = True
    echo_any = False
    skip_none_pair_keys = ('pos', 'size', 'size_hint', 'size_hint_min',
                           'size_hint_max')
    '''
    "The default size of a widget is (100, 100).
    This is only changed if the parent is a Layout."
    "The default size_hint is (1, 1). If the parent is a Layout,
    then the widget size will be the parent layout’s size."
    - <https://kivy.org/doc/stable/api-kivy.uix.widget.html>
    '''
    for try_attr in ['name', 'text', 'text_color', 'theme_text_color',
                     'md_bg_color', 'value', 'type', 'color',
                     'halign', 'valign', 'hor_growth', 'ver_growth',
                     'font_style', 'manager',
                     'pos',  # 'x', 'y',
                     'size',  # 'width', 'height',
                     'size_hint',  # 'size_hint_x', 'size_hint_y',
                     'size_hint_min',  # 'size_hint_min_x', 'size_hint_min_y',
                     'size_hint_max',  # 'size_hint_max_x', 'size_hint_max_y',
                     'width, height', 'source', 'icon', 'icon_size',
                     'active', 'disabled', 'icon_color', 'orientation',
                     'padding', 'spacing',
                     'width_mult', 'halign', 'valign',
                     'position',  # Not verified to exist (may be in KivyMD)
                     'pos_hint']:  # pos_hint is a dict (*not* list) Property
        # NOTE: id is done differently further up.
        '''
        ^ Ignore size_hint since "size_hint is a ReferenceListProperty of
           (size_hint_x, size_hint_y) properties."
           & ignore others structured similarly: size_hint_max, size
           (AliasProperty of width, height), and:
           - "right is an AliasProperty of (x + width)."
           - "top is an AliasProperty of (y + height)."
        ^ Ignore the following since result is not intended to be
          an operable app, just working KV code for prototyping in a
          visual editor:
          items, exit_manager, select_path,
          select_directory_on_press_button,
          select_directory_on_press_button, previous,
          and any events such as on_press.
        '''
        if (hasattr(widget, try_attr)
                and (getattr(widget, try_attr) is not None)):
            value = getattr(widget, try_attr)
            kv_value_str = None
            # There is no need to write the default for the following
            #   attributes:
            if try_attr == 'disabled':
                if value is False:
                    continue
            if try_attr == 'icon':
                if len(value) == 0:
                    continue
            if try_attr == 'icon_size':
                if value == 0:
                    continue
            if try_attr == 'valign':
                if value == 'bottom':
                    continue
            # The default value of halign isn't clear. The documentation
            #   says it is auto and left (contradictory):
            #   <https://kivy.org/doc/stable/api-kivy.uix.label.html#kivy.uix.label.Label.halign>
            if try_attr == 'spacing':
                if value == 0:
                    continue
            if try_attr == 'padding':
                nonzero_found = False
                for sub_value in value:
                    if sub_value != 0:
                        nonzero_found = True
                        break
                if not nonzero_found:
                    # There is no need to write the line. 0,0,0,0 is the
                    # default.
                    continue
            if try_attr == 'md_bg_color':
                if value == [1, 1, 1, 0]:
                    continue
            if try_attr in skip_none_pair_keys:
                if (value[0] is None) and (value[1] is None):
                    continue
                elif (try_attr == 'size_hint'):
                    if (value[0] == 1.0) and (value[1] == 1.0):
                        # 1.0, 1.0 is the default!
                        continue
                elif (try_attr == 'pos'):
                    if (value[0] == 0) and (value[1] == 0):
                        # 0, 0 is the default!
                        continue
                elif (try_attr == 'size'):
                    if (value[0] == 100) and (value[1] == 100):
                        # 100, 100 is the default!
                        continue
            elif try_attr.endswith("manager"):
                # Probably only 'manager' will work here, since
                #   something else like 'exit_manager' is defined in
                #   Python not KV as of KivyMD documentation accessed
                #   April 24, 2023:
                #   <kivymd.readthedocs.io/en/latest/components/filemanager/>
                if value is None:
                    continue
                manager_id = get_widget_id(value)
                if manager_id is None:
                    continue
                value = manager_id
            kv_value_str = property_to_kv_value(value)
            if kv_value_str is not None:
                outfn(child_indent + "{}: {}"
                      "".format(try_attr, kv_value_str))
                echo_any = True

    if not echo_any:
        outfn(indent + "# ^ (nondescript widget)")
    return True
