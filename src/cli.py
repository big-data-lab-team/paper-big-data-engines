import os

import click

engine_choices = click.argument("engine", type=click.Choice(["spark", "dask", "ray"]))
block_size = click.argument("block_size", type=click.Choice(["5000", "2500", "1000"]))


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
@click.option(
    "-b",
    "--benchmark-folder",
    type=click.Path(dir_okay=True, writable=True),
)
@engine_choices
@click.pass_context
def cli(
    ctx, input_folder, output_folder, scheduler, n_worker, benchmark_folder, engine
):
    ctx.ensure_object(dict)

    ctx.obj["INPUT_FOLDER"] = os.path.abspath(input_folder)
    ctx.obj["OUTPUT_FOLDER"] = os.path.abspath(output_folder)
    ctx.obj["N_WORKER"] = n_worker
    ctx.obj["BENCHMARK_FOLDER"] = benchmark_folder
    ctx.obj["SCHEDULER"] = scheduler
    ctx.obj["ENGINE"] = engine


@cli.command()
@block_size
@click.argument("iterations", type=int)
@click.argument("delay", type=float)
@click.pass_context
def increment(ctx, block_size, iterations, delay):
    run = import_from(f"app.{ctx.obj['ENGINE']}.increment", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        n_worker=ctx.obj["N_WORKER"],
        benchmark_folder=ctx.obj["BENCHMARK_FOLDER"],
        block_size=block_size,
        iterations=iterations,
        delay=delay,
    )


@cli.command()
@click.option("-r", "--random-seed", type=int, default=1234)
@block_size
@click.argument("iterations", type=int)
@click.argument("delay", type=float)
@click.pass_context
def multi_increment(ctx, block_size, random_seed, iterations, delay):
    run = import_from(f"app.{ctx.obj['ENGINE']}.multi_increment", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        n_worker=ctx.obj["N_WORKER"],
        benchmark_folder=ctx.obj["BENCHMARK_FOLDER"],
        block_size=block_size,
        iterations=iterations,
        delay=delay,
        seed=random_seed,
    )


@cli.command()
@block_size
@click.pass_context
def histogram(ctx, block_size):
    run = import_from(f"app.{ctx.obj['ENGINE']}.histogram", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        n_worker=ctx.obj["N_WORKER"],
        benchmark_folder=ctx.obj["BENCHMARK_FOLDER"],
        block_size=block_size,
    )


@cli.command()
@block_size
@click.argument("iterations", type=int)
@click.pass_context
def kmeans(ctx, block_size, iterations):
    run = import_from(f"app.{ctx.obj['ENGINE']}.kmeans", "run")

    run(
        input_folder=ctx.obj["INPUT_FOLDER"],
        output_folder=ctx.obj["OUTPUT_FOLDER"],
        scheduler=ctx.obj["SCHEDULER"],
        n_worker=ctx.obj["N_WORKER"],
        benchmark_folder=ctx.obj["BENCHMARK_FOLDER"],
        block_size=block_size,
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
        benchmark_folder=ctx.obj["BENCHMARK_FOLDER"],
        container_path=container,
    )


if __name__ == "__main__":
    cli()
