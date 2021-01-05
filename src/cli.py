import os

import click

engine_choices = click.argument("engine", type=click.Choice(["spark", "dask", "ray"]))


def import_from(module, name):
    module = __import__(module, fromlist=[name])
    return getattr(module, name)


@click.group()
@click.option(
    "-i",
    "--input-folder",
    required=True,
    type=click.Path(exists=True, dir_okay=True, readable=True),
)
@click.option(
    "-o",
    "--output-folder",
    required=True,
    type=click.Path(exists=True, dir_okay=True, writable=True),
)
@click.option("-s", "--scheduler", required=True)
@click.option("--benchmark", is_flag=True)
@engine_choices
@click.pass_context
def cli(ctx, input_folder, output_folder, scheduler, benchmark, engine):
    ctx.ensure_object(dict)

    ctx.obj["INPUT_FOLDER"] = os.path.abspath(input_folder)
    ctx.obj["OUTPUT_FOLDER"] = os.path.abspath(output_folder)
    ctx.obj["BENCHMARK"] = benchmark
    ctx.obj["SCHEDULER"] = scheduler
    ctx.obj["ENGINE"] = engine


@cli.command()
@click.argument("iterations", type=int)
@click.argument("delay", type=int)
@click.pass_context
def increment(ctx, iterations, delay):
    run = import_from(f"app.{ctx.obj['ENGINE']}.increment", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        benchmark=ctx.obj["BENCHMARK"],
        iterations=iterations,
        delay=delay,
    )


@cli.command()
@click.argument("iterations", type=int)
@click.argument("delay", type=int)
@click.pass_context
def multi_increment(ctx, iterations, delay):
    run = import_from(f"app.{ctx.obj['ENGINE']}.multi_increment", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        benchmark=ctx.obj["BENCHMARK"],
        iterations=iterations,
        delay=delay,
    )


@cli.command()
@click.pass_context
def histogram(ctx):
    run = import_from(f"app.{ctx.obj['ENGINE']}.histogram", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        benchmark=ctx.obj["BENCHMARK"],
    )


@cli.command()
@click.pass_context
def kmeans(ctx):
    run = import_from(f"app.{ctx.obj['ENGINE']}.kmeans", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        benchmark=ctx.obj["BENCHMARK"],
    )


@cli.command()
@click.pass_context
def bids_app(ctx):
    run = import_from(f"app.{ctx.obj['ENGINE']}.bids_app", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        benchmark=ctx.obj["BENCHMARK"],
    )
