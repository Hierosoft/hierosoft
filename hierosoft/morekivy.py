def property_to_kv_value(property):
    '''
    Change a real Python type value to a KV-encoded value,
    adding quotes if StringProperty or string.
    NOTE: id should *not* have quotes, so convert id using
    str(property) (or implicit conversion to str) *not* this function.
    '''
    if type(property).__name__ == "ReferenceListProperty":
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
          or (type(property).__name__ == "string")):
        return "'{}'".format(property.replace("'", "\\'"))
    if type(property).__name__ == "dp":
        return "{}dp".format(float(property))
    return str(property)
    # ^ else Python-like dict representation is ok for pos_hint in kvlang
    #   (See <https://stackoverflow.com/a/45100701/4541104>).


def widget_to_kv(widget, indent, widget_id=None, outfn=print):
    '''
    Show information about one widget, for debugging purposes.
    This method is designed to translate Python-generated
    widgets into KV (kvlang code).

    The resulting KV shown on the console can
    be used with https://github.com/kivymd/KivyMDBuilder, then
    the resulting KV can be translated back into the Python
    calls of the given ids (managed by SinglePage instances in
    this App).

    Keyword arguments:
    widget_id -- Specify a dictionary key or variable name in
        (from the App) which is used to access this
        widget. This will be used as the "id" in the KV file.
        Otherwise, id will be ignored (since this method assumes
        that the widgets were dynamically generated in a py
        file rather than a kv file which has ids)
    outfn -- The output function (print to console by default).
    '''
    if widget is None:
        outfn(indent + "# None")
        if widget_id is not None:
            outfn(indent + "#     id: {}".format(widget_id))
        return False
    outfn(indent + type(widget).__name__ + ":")
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
    for try_attr in ['text', 'text_color', 'theme_text_color',
                     'md_bg_color', 'value', 'type', 'color',
                     'halign', 'valign', 'hor_growth', 'ver_growth',
                     'font_style',
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
          an operable app, just working KV code for prototyping in a visual editor:
          items, exit_manager, select_path, select_directory_on_press_button,
          select_directory_on_press_button, previous
          and on_press and other events
        '''
        if hasattr(widget, try_attr) and (getattr(widget, try_attr) is not None):
            value = getattr(widget, try_attr)
            if try_attr in skip_none_pair_keys:
                if (value[0] is None) and (value[1] is None):
                    continue
                elif (try_attr == 'size_hint'):
                    if (value[0] == 1.0) and (value[1] == 1.0):
                        # 1.0, 1.0 is the default!
                        continue
                elif (try_attr == 'size'):
                    if (value[0] == 100) and (value[1] == 100):
                        # 100, 100 is the default!
                        continue
            outfn(child_indent + "{}: {}"
                  "".format(try_attr, property_to_kv_value(value)))
            echo_any = True

    if not echo_any:
        outfn(indent + "# ^ (nondescript widget)")
    return True