import click

from .post_process.assess_prioritisation import assess_prioritisation
from .prepare.create_batch_commands import prepare_exomiser_batch


@click.group()
def main():
    """PhEval - A benchmarking CLI."""


main.add_command(prepare_exomiser_batch)
main.add_command(assess_prioritisation)


if __name__ == "__main__":
    main()
