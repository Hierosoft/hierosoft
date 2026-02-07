
# -*- coding: utf-8 -*-
# import os
import sys

from hierosoft.hierosoftrepo import (
    generate_combined_license,
    pack_text,
)


def main():
    # if os.path.isfile(generated_path):
    #     os.remove(generated_path)
    # ^ Redundant due to FIRST logic in append_to_license
    pack_text()
    return generate_combined_license()


if __name__ == "__main__":
    sys.exit(main())
