"""Exomiser Runner"""
from dataclasses import dataclass

import click
from pheval.runners.runner import PhEvalRunner


@dataclass
class ExomiserPhEvalRunner(PhEvalRunner):
    """_summary_"""

    inputdir: click.Path
    testdatadir: click.Path
    tmpdir: click.Path
    outputdir: click.Path
    config: click.Path

    def prepare(self):
        """prepare"""
        print("preparing")

    def run(self):
        """run"""
        print("running with exomiser")

    def post_process(self):
        """post_process"""
        print("post processing")
