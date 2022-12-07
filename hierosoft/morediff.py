# -*- coding: utf-8 -*-

def get_diff_lines(before_path, after_path, strip=True):
    '''
    Get the lines that differ from one to the other in a form similar
    to a patch such as:

    -old line
    +new line

    The line appearing in a different place will *not* cause a diff.

    The line order is guaranteed except lines that appear more than once
    in either or both files.
    '''

    with open(before_path, 'r') as f1:
        temp1 = f1.readlines()
    with open(after_path, 'r') as f2:
        temp2 = f2.readlines()
    lines_of_files = [
        temp1,
        temp2,
    ]

    removed = {}
    added = {}
    diffs_of_files = [
        removed,
        added,
    ]

    if strip:
        for file_i in range(len(lines_of_files)):
            for i in range(len(lines_of_files[file_i])):
                lines_of_files[file_i][i] = lines_of_files[file_i][i].strip()


    other_i = 0
    for file_i in range(len(lines_of_files)):
        counted = []
        other_i += 1
        if other_i >= len(diffs_of_files):
            other_i = 0
        for i in range(len(lines_of_files[file_i])):
            line = lines_of_files[file_i][i]
            if line not in counted:
                f0_count = lines_of_files[file_i].count(line)
                f1_count = lines_of_files[other_i].count(line)
                if f0_count > f1_count:
                    skipped_count = 0
                    skip_count = f1_count
                    for diff_i in range(len(lines_of_files[file_i])):
                        # Add several + or - lines if the count differs
                        # between the two files.
                        if lines_of_files[file_i][diff_i] != line:
                            # This is not the line that differs.
                            continue
                        if skipped_count < skip_count:
                            # Only skip matches.
                            skipped_count += 1
                            continue
                        diffs_of_files[file_i][str(diff_i)] = line
                    # ^ 0 is removed, 1 is added
    results = []
    for i in range(max(len(lines_of_files[0]), len(lines_of_files[1]))):
        old = removed.get(str(i))
        if old is not None:
            results.append("-{}".format(old))
        new = added.get(str(i))
        if new is not None:
            results.append("+{}".format(new))

    return results
