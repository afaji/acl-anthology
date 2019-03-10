#!/usr/bin/env python3
# Marcel Bollmann <marcel@bollmann.me>, 2019

"""Usage: create_bibtex.py [--importdir=DIR] [--exportdir=DIR] [-c] [--debug]

Creates .bib files for all papers in the Hugo directory.

Options:
  --importdir=DIR          Directory to import XML files from. [default: {scriptdir}/../import/]
  --exportdir=DIR          Directory to write exported files to.   [default: {scriptdir}/../hugo/data-export/]
  --debug                  Output debug-level log messages.
  -c, --clean              Delete existing files in target directory before generation.
  -h, --help               Display this helpful text.
"""

from docopt import docopt
from glob import glob
from lxml import etree
from tqdm import tqdm
import gzip
import logging as log
import io
import os

from anthology.utils import SeverityTracker
from anth2bib import printbib
from create_hugo_pages import check_directory


def create_bibtex(srcdir, trgdir, clean=False):
    """Creates .bib files for all papers."""
    if not check_directory("{}/papers".format(trgdir), clean=clean):
        return
    if not check_directory("{}/volumes".format(trgdir), clean=clean):
        return

    log.info("Creating BibTeX files for all papers...")
    with gzip.open(
        "{}/anthology.bib.gz".format(trgdir), "wt", encoding="utf-8"
    ) as file_full:
        for xmlfile in tqdm(glob("{}/*.xml".format(srcdir))):
            with open(xmlfile, "r") as f:
                tree = etree.parse(f)
            root = tree.getroot()
            volume_id = root.get("id")
            volume_dir = "{}/papers/{}/{}".format(trgdir, volume_id[0], volume_id[:3])
            if not os.path.exists(volume_dir):
                os.makedirs(volume_dir)
            with open(
                "{}/volumes/{}.bib".format(trgdir, volume_id), "w"
            ) as file_volume:
                for item in root.findall("paper"):
                    full_id = "{}-{}".format(volume_id, item.get("id"))
                    with open(
                        "{}/{}.bib".format(volume_dir, full_id), "w"
                    ) as file_paper:
                        # To avoid calling printbib multiple times, print into a
                        # StringIO buffer and output its contents to all {paper,
                        # volume, full} bibliography files
                        contents = io.StringIO()
                        printbib(item, root, file=contents)
                        contents = contents.getvalue()
                        file_paper.write(contents)
                        file_volume.write(contents)
                        file_volume.write("\n")
                        file_full.write(contents)
                        file_full.write("\n")


if __name__ == "__main__":
    args = docopt(__doc__)
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    if "{scriptdir}" in args["--importdir"]:
        args["--importdir"] = os.path.abspath(
            args["--importdir"].format(scriptdir=scriptdir)
        )
    if "{scriptdir}" in args["--exportdir"]:
        args["--exportdir"] = os.path.abspath(
            args["--exportdir"].format(scriptdir=scriptdir)
        )

    log_level = log.DEBUG if args["--debug"] else log.INFO
    log.basicConfig(format="%(levelname)-8s %(message)s", level=log_level)
    tracker = SeverityTracker()
    log.getLogger().addHandler(tracker)

    create_bibtex(args["--importdir"], args["--exportdir"], clean=args["--clean"])

    if tracker.highest >= log.ERROR:
        exit(1)
