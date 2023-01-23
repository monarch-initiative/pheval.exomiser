import click

from .post_process.post_process_results_format import post_process_exomiser_results
from .prepare.create_batch_commands import prepare_exomiser_batch


@click.group()
def main():
    """Exomiser runner."""


main.add_command(prepare_exomiser_batch)
main.add_command(post_process_exomiser_results)

if __name__ == "__main__":
    main()
