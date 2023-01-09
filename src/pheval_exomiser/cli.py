import click

from .post_process.assess_prioritisation import benchmark, benchmark_comparison
from .prepare.create_batch_commands import prepare_exomiser_batch


@click.group()
def main():
    """Exomiser runner."""


main.add_command(prepare_exomiser_batch)
main.add_command(benchmark)
main.add_command(benchmark_comparison)


if __name__ == "__main__":
    main()
