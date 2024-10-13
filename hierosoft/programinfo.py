import os


def clean_file_name(name):
    """Replace all non-alphanumeric characters with underscores."""
    return ''.join(c if c.isalnum() else '_' for c in name)


def is_dot_notation(name):
    if not name:
        print("[is_dot_notation] got {}".format(repr(name)))
        return False
    for ch in name:
        if not ch.isdigit():
            if not ch == ".":
                return False
    return True


def find_all_ch(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]


def split_version(name):
    # parts = name.split("-")
    # if isinstance(name, (list, tuple)):
    if not isinstance(name, str):
        raise TypeError("Expected str, got %s(%s)"
                        % (type(name).__name__, repr(name)))
    starts = find_all_ch(name, "-")
    if len(starts) == 1:
        if is_dot_notation(name[starts[0]+1:]):
            return name[:starts[0]], name[starts[0]+1:]
        else:
            # like something-git, so there is no version, only suffix
            return name[:starts[0]], "", name[starts[0]+1:]
    version_ii = -1  # index of index (index in starts)
    for i in range(len(starts)):
        if i + 1 >= len(starts):
            end_idx = len(name)
        else:
            end_idx = starts[i+1]
        if is_dot_notation(name[starts[i]+1:end_idx]):
            version_ii = i
            break
    if version_ii > -1:
        if len(starts) > version_ii + 1:
            name_i = 0
            version_i = starts[version_ii]
            version_end = starts[version_ii+1]
            suffix_i = version_end
            # ^ such as git in 6.0.0-git or {hash} in 6.0.0-{hash}
            return name[name_i:version_i], name[version_i+1:version_end], name[suffix_i+1:]
        return name[:starts[version_ii]], name[starts[version_ii]+1:]
    return (name, )


def path_split_all(path):
    parts = os.path.split(path)
    if parts[0]:
        if parts[0] == "/":
            return [parts[0], parts[1]]
        return path_split_all(parts[0]) + [parts[1]]
    return [parts[1]]


class ProgramInfo:
    def __init__(self):
        self.name = None
        self.version = None
        self.suffix = None  # such as git in 6.0.0-git
        self.path = None

    def set_path(self, path):
        self.path = path
        self.set_version_from_path(path)

    def version_tuple(self):
        if not self.version:
            return None
        if not is_dot_notation(self.version):
            return None
        return tuple([int(num) for num in self.version.split(".")])

    def set_version_from_path(self, path):
        ancestors = path_split_all(path)
        ancestors_versions = []
        versioned_i = -1
        version = ""
        suffixed_i = -1
        suffix = ""
        for i, ancestor in enumerate(ancestors):
            ancestors_version = split_version(ancestor)
            if (len(ancestors_version) >= 2
                    and (len(ancestors_version[1].split("."))
                         > len(version))):
                versioned_i = i
                version = ancestors_version[1].split(".")
            if len(ancestors_version) >= 3:
                if len(ancestors_version[2]) > len(suffix):
                    suffixed_i = i
                    suffix = ancestors_version[2]
            ancestors_versions.append(ancestors_version)
        best_ancestor_i = 0
        if versioned_i > -1:
            best_ancestor_i = versioned_i
        elif suffixed_i > -1:
            best_ancestor_i = suffixed_i
        else:
            best_ancestor_i = len(ancestors) - 1
        name_and_version = ancestors[best_ancestor_i]
        parts = split_version(name_and_version)
        if len(parts) == 3:
            self.name = parts[0]
            self.version = parts[1]
            self.suffix = parts[2]
        elif len(parts) == 2:
            self.name = parts[0]
            self.version = parts[1]
        elif len(parts) == 1:
            self.name = parts[0]
        else:
            raise NotImplementedError(
                "name-version-suffix split incorrectly: {}".format(parts))
