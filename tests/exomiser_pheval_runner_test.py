"""CLI Test """
import logging
import unittest

from click.testing import CliRunner
from pheval.cli_pheval import run


class TestCommandLineInterface(unittest.TestCase):
    """
    Tests all command-line subcommands
    """

    def setUp(self) -> None:
        runner = CliRunner(mix_stderr=False)
        self.runner = runner

    def test_cli_exomiser(self):
        """test valid runner"""
        result = self.runner.invoke(
            run, ["-i", "./", "-t", "./", "-r", "exomiserphevalrunner", "-o", "./"]
        )
        err = result.stderr
        self.assertEqual(None, result.exception)
        logging.info("ERR=%s", err)
        exit_code = result.exit_code
        self.assertEqual(0, exit_code)
        self.assertTrue("running with exomiser" in result.stdout)

    def test_cli_invalid_runner(self):
        """test invalid runner"""
        result = self.runner.invoke(
            run, ["-i", "./", "-t", "./", "-r", "invalid_runner", "-o", "./"]
        )
        err = result.stderr
        self.assertTrue("Invalid PhEvalRunner name:" in str(result.exception))
        logging.info("ERR=%s", err)
        exit_code = result.exit_code
        self.assertEqual(1, exit_code)
