# join_if_exists

```
from hierosoft import join_if_exists
```

Simplifies:
```
correct_path = os.path.join("/opt", "mtanalyze")
try_path = os.path.join("/opt", "git", "mtanalyze")
if os.path.exists(try_path):
    correct_path = try_path
if os.path.exists(correct_path):
    print('Found "{}"'.format(correct_path))
else:
    print("Error: {} was not found.".format(correct_path))
    # ^ This error is misleading because correct_path isn't really
    #   correct (Its first value was).
```

or

```
try_paths = [os.path.join("/opt", "mtanalyze"), os.path.join("/opt", "git", "mtanalyze")]
got_path = None
for try_path in try_paths:
    if os.path.exists(try_path):
        got_path = try_path
        break

if got_path is not None:
    print('Found "{}"'.format(got_path))
else:
    print("Error: {} was not found.".format(try_paths[0]))
```

to

```Python
try_paths = [os.path.join("/opt", "mtanalyze"), os.path.join("/opt", "git", "mtanalyze")]
got_path = join_if_exists("/opt", try_paths)

if got_path is not None:
    print('Found "{}"'.format(got_path))
else:
    print("Error: {} was not found.".format(try_paths[0]))
```
