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
@click.option("-n", "--n-worker", type=int, default=1, required=False)
@click.option("--benchmark", is_flag=True)
@engine_choices
@click.pass_context
def cli(ctx, input_folder, output_folder, scheduler, n_worker, benchmark, engine):
    ctx.ensure_object(dict)

    ctx.obj["INPUT_FOLDER"] = os.path.abspath(input_folder)
    ctx.obj["OUTPUT_FOLDER"] = os.path.abspath(output_folder)
    ctx.obj["N_WORKER"] = n_worker
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
        n_worker=ctx.obj["N_WORKER"],
        benchmark=ctx.obj["BENCHMARK"],
        iterations=iterations,
        delay=delay,
    )


@cli.command()
@click.option("-r", "--random-seed", type=int, default=1234)
@click.argument("iterations", type=int)
@click.argument("delay", type=int)
@click.pass_context
def multi_increment(ctx, random_seed, iterations, delay):
    run = import_from(f"app.{ctx.obj['ENGINE']}.multi_increment", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        n_worker=ctx.obj["N_WORKER"],
        benchmark=ctx.obj["BENCHMARK"],
        iterations=iterations,
        delay=delay,
        seed=random_seed,
    )


@cli.command()
@click.pass_context
def histogram(ctx):
    run = import_from(f"app.{ctx.obj['ENGINE']}.histogram", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        n_worker=ctx.obj["N_WORKER"],
        benchmark=ctx.obj["BENCHMARK"],
    )


@cli.command()
@click.argument("iterations", type=int)
@click.pass_context
def kmeans(ctx, iterations):
    run = import_from(f"app.{ctx.obj['ENGINE']}.kmeans", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        n_worker=ctx.obj["N_WORKER"],
        benchmark=ctx.obj["BENCHMARK"],
        iterations=iterations,
    )


@cli.command()
@click.argument(
    "container", type=click.Path(exists=True, file_okay=True, readable=True)
)
@click.pass_context
def bids(ctx, container):
    run = import_from(f"app.{ctx.obj['ENGINE']}.bids", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        n_worker=ctx.obj["N_WORKER"],
        benchmark=ctx.obj["BENCHMARK"],
        container_path=container,
    )


if __name__ == "__main__":
    cli()