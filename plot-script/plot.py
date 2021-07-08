from collections import defaultdict
import glob
import os
import re

from bokeh.models import CustomJS, ColumnDataSource, Grid, LinearAxis, Plot, Range1d
from bokeh.models.annotations import Legend, LegendItem, Title
from bokeh.models.glyphs import Quad
from bokeh.models.tools import (
    BoxZoomTool,
    HoverTool,
    PanTool,
    ResetTool,
    SaveTool,
    TapTool,
    WheelZoomTool,
)
from bokeh.io import curdoc, output_file, output_notebook, reset_output, save, show
from bokeh.palettes import Colorblind8
import matplotlib
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def gantt(
    df,
    xlabel="Time [s]",
    *,
    pre_process,
    group,
    x_limit,
    save_name,
    framework,
    ylabel,
    title,
):
    """Create an interactive gantt chart from a pandas dataframe.

    Parameters
    ----------
    df : pandas.Dataframe
        Data to plot.
    pre_process : func
        Function to pre-process the dataframe.
    group : string, optional
        Column name of the element to group together.
    x_limit: int, optional
        Maximum value for the x axis.
    save_name : str, optional
        Filename for the gantt chart.
    framework : str
        Name of the framework from which the data were collected.
        Currently only support Dask and Spark.
    xlabel : str
        Label for the x axis.
    ylabel : str
        Label for the y axis.
    """
    if framework == "spark":
        df["thread"] = df["process"]

    if pre_process:
        df = pre_process(df)

    _MUST_HAVE_COLUMN = ["func", "start", "end", "filename", "thread", group]
    for column_name in _MUST_HAVE_COLUMN:
        try:
            if column_name not in df.columns:
                raise ValueError
        except ValueError:
            print(
                f"fatal error: the dataframe must contain '{column_name}' after the pre-processing."
            )
            return

    if x_limit is None:
        x_limit = df.end.max()

    plot = Plot(
        plot_width=1250 if save_name is not None else 800,
        plot_height=700 if save_name is not None else 600,
        x_range=Range1d(-x_limit * 0.05, x_limit * 1.05, bounds="auto"),
        y_range=Range1d(
            -max(len(df[group].unique()) * 0.05, 1),
            len(df[group].unique()) * 1.85,
            bounds="auto",
        ),
    )

    # Group the dataframe by user defined group.
    # Create label and associate an y-axis value for each group.
    labels = []
    for i, x in enumerate(df.groupby(group, sort=False)):
        labels.append(x[0])
        df.loc[df.index.isin(x[1].index), "bottom"] = i * 1.5

    for i, worker_name in enumerate(sorted(df.worker_name.unique())):
        df.loc[df.worker_name == worker_name, "bottom"] += 16 * i
    df["top"] = df["bottom"] + 1

    # Define color map for the functions.
    glyphs = list()
    for i, x in enumerate(sorted(df.func.unique())):
        color = Colorblind8[i % len(Colorblind8)]
        df.loc[df.func == x, "color"] = color

        glyphs.append(
            plot.add_glyph(
                ColumnDataSource({}),
                Quad(
                    fill_color=color,
                    fill_alpha=0.66,
                    line_color=color,
                    line_width=0.75,
                ),
            )
        )
    df["original_color"] = df["color"]

    df["runtime"] = df.end - df.start

    source = ColumnDataSource(df)

    glyph = Quad(
        left="start",
        right="end",
        top="top",
        bottom="bottom",
        fill_color="color",
        fill_alpha=0.66,
        line_color="color",
        line_width=0.75,
    )

    l = plot.add_glyph(source, glyph)

    # Legend
    legend = Legend(
        items=[
            LegendItem(label=func, renderers=[glyphs[i]])
            for i, func in enumerate(sorted(df.func.unique()))
        ]
    )
    plot.add_layout(legend, "above")
    plot.legend.orientation = "horizontal"

    if title:
        t = Title()
        t.text = f"{len(df[group].unique())} {ylabel}: {title}"
        plot.title = t

    # Axis
    xaxis = LinearAxis()
    plot.add_layout(xaxis, "below")
    plot.xaxis.axis_label = xlabel

    yaxis = LinearAxis()
    plot.add_layout(yaxis, "left")
    plot.yaxis.axis_label = ylabel
    plot.yaxis.major_label_text_font_size = (
        "6pt"  # Reduce font size to fit all group together.
    )

    plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
    plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))

    # Set y axis tick label
    #     plot.yaxis.ticker = list(range(0, len(labels)))
    #     plot.yaxis.major_label_overrides = {k: "" for k, v in zip(range(0, len(labels)), labels)}
    plot.yaxis.major_tick_line_color = None
    plot.yaxis.minor_tick_line_color = None
    plot.yaxis.major_label_text_font_size = "0pt"

    # Hover tool
    hover = HoverTool(
        tooltips=[
            ("filename", "@filename"),
            ("hostname", "@hostname"),
            ("worker", f"@{group}"),
            ("function", "@func"),
            ("runtime", "@runtime{0.3f} sec"),
            ("start time", "@start{0.3f} sec"),
            ("end time", "@end{0.3f} sec"),
        ],
        formatters={
            "runtime": "printf",
            "start": "printf",
            "end": "printf",
        },
        #         attachment="left",
    )

    # Tap tool custom select
    cb_click = CustomJS(
        args=dict(source=source),
        code="""
        const indices = source.selected.indices;
        const data = source.data;

        const same_file = new Set();
        for (var i=0; i < data['color'].length; i++){
            data['color'][i] = data['original_color'][i];
            for (var j=0; j < indices.length; j++){
                if (data['filename'][i] == data['filename'][indices[j]]){
                    data['color'][i] = "blueviolet";
                    same_file.add(i);
                }
            }
        }
        
        source.selected.indices = Array.from(same_file);
        source.change.emit();
    """,
    )
    source.selected.js_on_change("indices", cb_click)

    ## Tool
    plot.add_tools(BoxZoomTool())
    plot.add_tools(hover)
    plot.add_tools(PanTool())
    plot.add_tools(ResetTool())
    plot.add_tools(SaveTool())
    plot.add_tools(TapTool(callback=cb_click))
    plot.add_tools(WheelZoomTool())

    curdoc().add_root(plot)

    # Display mode
    if save_name:
        reset_output()
        os.makedirs(os.path.dirname(save_name), exist_ok=True)
        output_file(save_name)
        save(plot)
    else:
        reset_output()
        output_notebook()
        show(plot)


def wasted_time(df, *, framework):
    if framework == "spark":
        df["thread"] = df["process"]

    core_used = sum(
        [
            1
            for w in df.worker.unique()
            for i, t in enumerate(df[df.worker == w].thread.unique())
        ]
    )

    df["runtime"] = df.end - df.start
    function_time = df.groupby("func")["runtime"].sum()

    run_time = []
    for function in sorted(df["func"].unique()):
        run_time.append(function_time[function])

    total_time = df.end.max() * core_used

    wasted_time = total_time - sum(run_time)
    return wasted_time, *run_time


def idle_time(df, *, framework):
    if framework == "spark":
        df["thread"] = df["process"]

    by_thread = df.groupby(["worker", "thread"])

    df["runtime"] = df.end - df.start
    function_time = df.groupby("func")["runtime"].sum()

    run_time = []
    for function in sorted(df["func"].unique()):
        run_time.append(function_time[function])

    thread_runtimes = by_thread["runtime"].sum()
    thread_completion = by_thread["end"].max()

    idle_time = (thread_completion - thread_runtimes).sum()
    return idle_time, *run_time


def stacked_bar(
    *,
    idle_func,
    col_names,
    benchmark_dir,
    experiment,
    parameters,
    xlabel,
    save_name=None,
    ylim=None,
    title=None,
    **kwargs,
):
    matplotlib.rcParams.update({"font.size": 22})

    HATCHES = ["//", "\\\\", "||", "--", "++", "xx", "oo", "OO", "..", "**"]

    fig, ax = plt.subplots(figsize=(20, 10))
    bar_width = 0.2

    benchmark_dir += f"/*{experiment}"
    freedom = None
    for parameter in parameters:
        if parameter in kwargs:
            benchmark_dir += f":{parameter}={kwargs[parameter]}"
        else:
            assert freedom == None, "Only one degree of freedom is allowed."
            benchmark_dir += f":{parameter}=*"
            freedom = parameter

    print(f"{benchmark_dir=}")
    filenames = glob.glob(benchmark_dir + "/*summary-*.csv")

    xticks_label = sorted(
        {
            float(x.replace(freedom + "=", ""))
            for k in filenames
            for x in k.split("/")[-2].split(":")[2:]
            if freedom in x
        }
    )
    x_pos = lambda i: np.arange(len(xticks_label)) + bar_width * i

    results = defaultdict(lambda: defaultdict(list))
    for x in filenames:
        path = x.split("/")
        experiment = path[-2]

        framework = experiment.split(":")[0]
        results[framework][experiment].append(x)

    # Application makespan
    for summary_xs, (framework, experiments) in enumerate(sorted(results.items())):
        data = [
            [
                pd.read_csv(file_, names=col_names).end.max()
                for file_ in experiments[key]
            ]
            for key in sorted(
                experiments,
                key=lambda k: float(re.search(f"{freedom}=(\d+\.?\d*)", k).group(1)),
            )
        ]

        stats = {
            "mean": list(map(np.mean, data)),
            "std": list(map(np.std, data)),
        }
        y_offset = max(stats["mean"]) * 0.01
        totals = stats["mean"]
        color = Colorblind8[summary_xs % len(Colorblind8)]

        ############
        # Plotting #
        ############
        ax.bar(
            x_pos(summary_xs),
            stats["mean"],
            yerr=stats["std"],
            color=color,
            width=bar_width,
            edgecolor="black",
            alpha=1,
            #             label=framework.capitalize(),
        )

        # Annotate bar height
        for x, total in zip(x_pos(summary_xs), totals):
            ax.text(
                x,
                total + y_offset,
                round(total),
                ha="center",
                weight="bold",
                fontsize=14,
                color=color,
            )

    # Application detailed time spent
    ax2 = ax.twinx()
    for detailed_xs, (framework, experiments) in enumerate(sorted(results.items())):
        data = [
            np.array(
                [
                    idle_func(pd.read_csv(file_, names=col_names), framework=framework)
                    for file_ in experiments[key]
                ]
            )
            for key in sorted(
                experiments,
                key=lambda k: float(re.search(f"{freedom}=(\d+\.?\d*)", k).group(1)),
            )
        ]

        stats = {
            "mean": np.array([x.mean(axis=0) for x in data]).T,
            "std": np.array([x.std(axis=0) for x in data]).T,
        }
        print(f"{framework}:\n{stats['mean'][::-1]}")

        ############
        # Plotting #
        ############
        y_offset = stats["mean"].max() * 0.01
        totals = stats["mean"].sum(axis=0)
        color = Colorblind8[detailed_xs % len(Colorblind8)]
        # Plot idle time as a special case since it always exist.
        # Thus we want to having consistent hatch and position.
        ax2.bar(
            x_pos(detailed_xs + summary_xs + 1),
            stats["mean"][0],
            yerr=stats["std"][0],
            color=color,
            hatch=HATCHES[0],  # Set different hatch for the bar stacks
            width=bar_width,
            edgecolor="black",
            alpha=0.66,
            #             label=framework.capitalize(),
        )

        y_bottom = stats["mean"][0]

        for j in range(1, len(stats["mean"][1:]) + 1):
            ax2.bar(
                x_pos(detailed_xs + summary_xs + 1),
                stats["mean"][j],
                yerr=stats["std"][j],
                bottom=y_bottom,
                color=color,
                hatch=HATCHES[
                    j % len(HATCHES)
                ],  # Set different hatch for the bar stacks
                width=bar_width,
                edgecolor="black",
                alpha=0.66,
            )
            y_bottom += stats["mean"][j]

        # Annotate bar height
        for x, total in zip(x_pos(detailed_xs + summary_xs + 1), totals):
            ax2.text(
                x,
                total + y_offset,
                round(total),
                ha="center",
                weight="bold",
                fontsize=14,
                color=color,
            )

    xticks_loc = (
        np.arange(len(xticks_label)) + bar_width * (detailed_xs + summary_xs + 1) / 2
    )
    plt.xticks(xticks_loc, xticks_label)
    ax.set_xlabel(xlabel, fontweight="bold")
    ax.set_ylabel("Makespan [s]", fontweight="bold")
    ax2.set_ylabel("Total time [s]", fontweight="bold")

    if ylim:
        plt.ylim([0, ylim])

    plt.title(title)

    # Total time legend (Summary)
    patches = []
    for i, (framework, _) in enumerate(sorted(results.items())):
        patches.append(
            Patch(
                facecolor=Colorblind8[i % len(Colorblind8)],
                edgecolor="black",
                label=framework.capitalize(),
            )
        )
    legend_1 = plt.legend(
        handles=patches,
        loc="upper left",
        bbox_to_anchor=(0, -0.05),
        title="Makespan [s]",
    )
    plt.gca().add_artist(legend_1)

    # Makespan legend (Detailed)
    framework_patches = []
    for i, (framework, _) in enumerate(sorted(results.items())):
        framework_patches.append(
            Patch(
                facecolor=Colorblind8[i % len(Colorblind8)],
                alpha=0.66,
                edgecolor="black",
                label=framework.capitalize(),
            )
        )

    func_patches = []
    sample_df = pd.read_csv(filenames[0], names=col_names)
    for i, function in enumerate(["idle"] + sorted(sample_df["func"].unique())):
        func_patches.append(
            Patch(
                facecolor="lightgray",
                hatch=HATCHES[i % len(HATCHES)],
                label=function.capitalize(),
            )
        )

    delta = abs(len(func_patches) - len(framework_patches))
    if len(func_patches) > len(framework_patches):
        framework_patches += [Patch(alpha=0)] * delta
    elif len(framework_patches) > len(func_patches):
        func_patches = [Patch(alpha=0)] * delta + func_patches

    plt.legend(
        handles=(framework_patches + func_patches[::-1]),
        loc="upper right",
        bbox_to_anchor=(1, -0.05),
        ncol=2,
        title="Total time [s]",
    )

    if save_name:
        plt.title("")  # Remove title for used with Latex Fig.
        os.makedirs(os.path.dirname(save_name), exist_ok=True)
        plt.savefig(save_name, bbox_inches="tight")
        plt.title(title)

    plt.show()
