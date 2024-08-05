import os
from csv import reader

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np


def set_figure_size(fig, w, h):
    l = fig.subplotpars.left
    r = fig.subplotpars.right
    t = fig.subplotpars.top
    b = fig.subplotpars.bottom
    figw = float(w) / (r - l)
    figh = float(h) / (t - b)
    fig.set_size_inches(figw, figh)


def write_to_figure(fig, folder_path, fig_name):
    os.makedirs(folder_path, exist_ok=True)
    fig_path = folder_path + "/" + fig_name
    print('writing to figure... ' + fig_path)
    fig.savefig(fig_path)


def plot_varying_timeout():
    # csv schema: time, event
    # where:
    # time is in seconds
    # event can be counterexample
    csv_path_prefix = "varying_timeout_"

    leetcode_workload = "LeetCode"
    calcite_workload = "Calcite"
    literature_worklaod = "Literature"

    workloads = [leetcode_workload, calcite_workload, literature_worklaod]
    # workloads = [leetcode_workload,]

    workload_to_total = {
        leetcode_workload: 10,
        calcite_workload: 397,
        literature_worklaod: 64,
    }

    for workload in workloads:

        csv_path = csv_path_prefix + workload + ".csv"
        total = workload_to_total[workload]
        not_checked_xs = [0]
        not_checked_ys = [0]

        # read in data
        with open(csv_path, 'r') as read_obj:
            next(read_obj)
            csv_reader = reader(read_obj)
            for row in csv_reader:
                time = float(row[0])
                event = str(row[1])
                if (event == "counterexample"):
                    not_checked_xs.append(time)
                    not_checked_ys.append(not_checked_ys[-1] + 1)
                else:
                    assert False

            fig, ax = plt.subplots()

        ax.plot(
            not_checked_xs,
            not_checked_ys,
            linewidth=2,
        )

        ax.yaxis.set_visible(True)

        ax.spines['top'].set_visible(False)
        # ax.spines['bottom'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(True)
        # fig.tight_layout()

        set_figure_size(fig, 12, 5.5)
        ax.yaxis.set_label_coords(0.13, 1.05)
        ax.tick_params(axis='x', which='major', pad=1)
        ax.tick_params(axis='y', which='major', pad=10)
        plt.subplots_adjust(top=.88, bottom=0.3, right=.99, left=0.08)

        fig_name = "varying_timeout_" + workload + ".pdf"
        write_to_figure(fig, "results", fig_name)


def plot_varying_bound_1():
    # csv schema: bound, number of checked benchmarks, average time, median time
    # number of checked benchmarks: those that can terminate within the given timeout
    # average time: among those terminated
    # median time: among those terminated
    csv_path_prefix = "varying_bound_"

    leetcode_workload = "LeetCode"
    calcite_workload = "Calcite"
    literature_worklaod = "Literature"

    workloads = [leetcode_workload, calcite_workload, literature_worklaod]

    workload_to_total = {
        leetcode_workload: 32780,
        calcite_workload: 397,
        literature_worklaod: 64,
    }

    for workload in workloads:

        csv_path = csv_path_prefix + workload + ".csv"
        total = workload_to_total[workload]

        bounds = []
        average_time_ys = []
        median_time_ys = []
        num_checked_benchmarks = []

        # read in data
        with open(csv_path, 'r') as read_obj:
            next(read_obj)
            csv_reader = reader(read_obj)
            for row in csv_reader:
                bounds.append(int(row[0]))
                num_checked_benchmarks.append(int(row[1]))
                average_time_ys.append(float(row[2]))
                median_time_ys.append(float(row[3]))

        fig, ax = plt.subplots()

        ax.set_xlabel("bound")
        ax.set_ylabel("# of checked benchmarks", rotation=0)

        ax.spines['top'].set_visible(False)
        # ax.spines['bottom'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(True)
        # fig.tight_layout()
        ax.set_yscale('log')

        ax.set_xlim([1, 5])

        ax.plot(
            bounds,
            num_checked_benchmarks,
            linewidth=2,
        )

        # ax.legend()

        set_figure_size(fig, 12, 5.5)
        ax.yaxis.set_label_coords(0.13, 1.05)
        ax.tick_params(axis='x', which='major', pad=1)
        ax.tick_params(axis='y', which='major', pad=10)
        plt.subplots_adjust(top=.88, bottom=0.3, right=.99, left=0.08)

        fig_name = "varying_bound_" + workload + ".pdf"
        write_to_figure(fig, "results", fig_name)


def plot_varying_bound():
    # csv schema: bound, number of checked benchmarks, average time, median time
    # number of checked benchmarks: those that can terminate within the given timeout
    # average time: among those terminated
    # median time: among those terminated
    csv_path_prefix = "varying_bound_"

    leetcode_workload = "LeetCode"
    calcite_workload = "Calcite"
    literature_worklaod = "Literature"

    workloads = [leetcode_workload, calcite_workload, literature_worklaod]
    bounds = range(1, 11)

    workload_bound_to_results = {
        workload: {
            i: [] for i in bounds
        } for workload in workloads
    }

    for workload in workloads:

        csv_path = csv_path_prefix + workload + ".csv"

        # read in data
        with open(csv_path, 'r') as read_obj:
            next(read_obj)
            csv_reader = reader(read_obj)
            for row in csv_reader:
                bound = int(row[0])
                results = []
                results.append(int(row[1]))
                results.append(round(float(row[2]), 1))
                results.append(round(float(row[3]), 1))
                workload_bound_to_results[workload][bound] = results

    for bound in bounds:
        row = str(bound)
        for workload in workloads:
            results = workload_bound_to_results[workload][bound]
            num = results[0]
            avg = results[1]
            median = results[2]
            row += " & " + str(num) + " & " + str(avg) + " & " + str(median)
        row += "\n\\\\"
        print(row)


def plot_operation_performance():
    pass


def plot_cex():
    # csv schema: tool, workload, total, genuine
    csv_path = "counterexamples.csv"

    leetcode_workload = "LeetCode"
    calcite_workload = "Calcite"
    literature_worklaod = "Literature"

    workloads = [leetcode_workload, calcite_workload, literature_worklaod]

    VeriEQL_tool_RQ1 = "VeriEQL-RQ1"
    VeriEQL_tool_RQ2 = "VeriEQL-RQ2"
    Cosette_tool_RQ1 = "Cosette-RQ1"
    Cosette_tool_RQ2 = "Cosette-RQ2"
    Qex_tool_RQ1 = "Qex-RQ1"
    Qex_tool_RQ2 = "Qex-RQ2"
    DataFiller_tool_RQ1 = "DataFiller-RQ1"
    DataFiller_tool_RQ2 = "DataFiller-RQ2"
    XData_tool_RQ1 = "XData-RQ1"
    XData_tool_RQ2 = "XData-RQ2"

    tools = [
        VeriEQL_tool_RQ1,
        VeriEQL_tool_RQ2,
        Cosette_tool_RQ1,
        Cosette_tool_RQ2,
        Qex_tool_RQ1,
        Qex_tool_RQ2,
        DataFiller_tool_RQ1,
        DataFiller_tool_RQ2,
        XData_tool_RQ1,
        XData_tool_RQ2,
    ]

    tool_to_axis_label = {
        VeriEQL_tool_RQ1: "VeriEQL",
        VeriEQL_tool_RQ2: "VeriEQL\n  -noIC",
        Cosette_tool_RQ1: "Cosette",
        Cosette_tool_RQ2: "Cosette\n  -noIC",
        Qex_tool_RQ1: "Qex",
        Qex_tool_RQ2: "Qex\n  -noIC",
        DataFiller_tool_RQ1: "DataFiller",
        DataFiller_tool_RQ2: "DataFiller\n  -noIC",
        XData_tool_RQ1: "XData",
        XData_tool_RQ2: "XData\n  -noIC",
    }

    types = ["all", "genuine"]

    # each entry maps (tool, workload, type) to the number of
    result = {}

    # read in data
    with open(csv_path, 'r') as read_obj:
        next(read_obj)
        csv_reader = reader(read_obj)
        for row in csv_reader:
            # complete this to populate the result
            num_total = float(row[2])
            num_genuine = float(row[3])
            result[(row[0], row[1], "all")] = num_total
            result[(row[0], row[1], "genuine")] = num_genuine

    # at this point, result is filled with all necessary data
    # now plot figures
    bar_width = 0.3
    num_bars_in_group = len(types)
    num_groups = len(tools)
    group_width = bar_width * num_bars_in_group
    width_between_groups = 0.2
    left_space = width_between_groups * 0.5
    right_space = left_space
    total_width_per_group = group_width + width_between_groups

    xs = np.array([i * total_width_per_group for i in range(0, num_groups)])

    bar_label_font_size = 30
    bar_label_padding = 5
    x_tick_label_font_size = 30
    y_tick_label_font_size = 30
    axis_label_font_size = 45
    legend_font_size = 45

    group_xs = xs + left_space + group_width / 2
    total_xs = xs + left_space + bar_width / 2
    genuine_xs = total_xs + bar_width

    xticks = group_xs
    xtick_labels = [tool_to_axis_label[tool] for tool in tools]

    for workload in workloads:
        # for each tool, map to a list of bar heights
        type_to_num_benchmarks = {type: [] for type in types}
        for type in types:
            for tool in tools:
                num_benchmarks = result[(tool, workload, type)]
                type_to_num_benchmarks[type].append(num_benchmarks)

        fig, ax = plt.subplots()

        total_bars = ax.bar(
            x=total_xs,
            height=type_to_num_benchmarks["all"],
            width=bar_width,
            label="all",
            color="white",
            edgecolor="black",
        )
        if workload == "LeetCode":
            bar_info = ax.bar_label(total_bars, padding=bar_label_padding,
                                    fontsize=20, rotation=0)
            bar_info[0].xyann = (-5, bar_info[0].xyann[-1])
            bar_info[6].xyann = (-5, bar_info[6].xyann[-1])
        else:
            ax.bar_label(total_bars, padding=bar_label_padding,
                         fontsize=bar_label_font_size, rotation=0)

        genuine_bars = ax.bar(
            x=genuine_xs,
            height=type_to_num_benchmarks["genuine"],
            width=bar_width,
            label="genuine",
            color='black',
            edgecolor="black",
        )
        if workload == "LeetCode":
            bar_info = ax.bar_label(genuine_bars, padding=bar_label_padding,
                                    fontsize=20, rotation=0)
            bar_info[0].xyann = (13, bar_info[0].xyann[-1])
            bar_info[1].xyann = (9, bar_info[1].xyann[-1])
            bar_info[6].xyann = (4, bar_info[6].xyann[-1])
            bar_info[7].xyann = (4, bar_info[7].xyann[-1])
        else:
            ax.bar_label(genuine_bars, padding=bar_label_padding,
                         fontsize=bar_label_font_size, rotation=0)

        ax.set_xticks(xticks)

        ax.yaxis.set_visible(True)
        ax.set_ylabel("# of benchmarks", rotation=0,
                      fontsize=axis_label_font_size)

        ax.set_xlim(0, genuine_xs[-1] + bar_width / 2 + right_space)
        ax.spines['top'].set_visible(False)
        # ax.spines['bottom'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(True)
        # fig.tight_layout()

        #
        # custom fields
        #
        ax.set_xticklabels(
            xtick_labels, fontsize=x_tick_label_font_size, rotation=60)

        if workload == 'LeetCode':
            # yticks = [0, 5000, 10000, 15000]
            yticks = [0, 5000, 10000, 15000]
            # ax.set_ylim([0, 20000])
            # ax.set_yscale('log')
            ytick_labels = ['0', '5k', '10k', '15k']
        else:
            yticks = [0, 10, 20, 30, 40, 50]
            ytick_labels = yticks
        ax.set_yticks(yticks)
        ax.yaxis.set_ticklabels(ytick_labels, fontsize=y_tick_label_font_size)

        set_figure_size(fig, 12, 5.5)
        ax.yaxis.set_label_coords(0.13, 1.1)
        ax.tick_params(axis='x', which='major', pad=1)
        ax.tick_params(axis='y', which='major', pad=10)
        if workload == "LeetCode":
            plt.subplots_adjust(top=.83, bottom=0.3, right=.99, left=0.12)
        else:
            plt.subplots_adjust(top=.83, bottom=0.3, right=.99, left=0.07)
        ax.legend(
            ncol=3,
            columnspacing=1,
            bbox_to_anchor=(.68, 1.3),
            # bbox_to_anchor=(-0.4, 0.5),
            loc='upper center',
            facecolor='white',
            framealpha=1,
            frameon=False,
            prop={'size': legend_font_size},
        )

        fig_name = "counterexamples_" + workload + ".pdf"
        write_to_figure(fig, "results", fig_name)


def plot_dist():
    # csv schema: tool, workload, total, genuine
    csv_path = "distribution.csv"

    # TOOLS = ["LeetCode", "Calcite", "Literature"]

    leetcode_workload = "LeetCode"
    calcite_workload = "Calcite"
    literature_worklaod = "Literature"

    workloads = [leetcode_workload, calcite_workload, literature_worklaod]
    # each entry maps (tool, workload, type) to the number of
    result = {leetcode_workload: [], calcite_workload: [], literature_worklaod: []}
    y_tick_labels = []

    # read in data
    with open(csv_path, 'r') as read_obj:
        next(read_obj)
        csv_reader = reader(read_obj)
        for row in csv_reader:
            # complete this to populate the result
            num_leetcode = float(row[1])
            num_calcite = float(row[2])
            num_literature = float(row[3])
            result[leetcode_workload].append(num_leetcode)
            result[calcite_workload].append(num_calcite)
            result[literature_worklaod].append(num_literature)
            y_tick_labels.append(row[0])
    for worklod in workloads:
        sum_sample = sum(result[worklod])
        tmp = [sum_sample]
        for num in result[worklod][:-1]:
            tmp.append(tmp[-1] - num)
        result[worklod] = tmp

    # at this point, result is filled with all necessary data
    # now plot figures
    bar_width = 0.3
    num_bars_in_group = 1
    num_groups = 1
    group_width = bar_width * num_bars_in_group
    width_between_groups = 0.2
    left_space = width_between_groups * 0.5
    right_space = left_space
    total_width_per_group = group_width + width_between_groups

    bar_label_font_size = 10
    bar_label_padding = 5
    x_tick_label_font_size = 13
    y_tick_label_font_size = 13
    axis_label_font_size = 15
    legend_font_size = 15

    fig = plt.figure()
    gs = gridspec.GridSpec(
        1,
        len(workloads) * 2 - 1,
        width_ratios=[3, 1, 3, 1, 3],
    )

    for subfigure_idx, workload in zip([0, 2, 4], workloads):
        ys = np.array([i * total_width_per_group for i in range(0, len(result[workload]))])
        total_ys = ys + left_space + bar_width / 2

        set_figure_size(fig, 10, 4)
        ax = fig.add_subplot(gs[0, subfigure_idx])
        ax.invert_yaxis()
        ax.xaxis.tick_top()

        total_bars = ax.barh(
            total_ys,
            result[workload],
            height=bar_width,
            label="all",
            color="black",
            # edgecolor="black",
        )
        if workload == "LeetCode":
            bar_info = ax.bar_label(total_bars, padding=bar_label_padding,
                                    fontsize=bar_label_font_size, rotation=0)
        else:
            bar_info = ax.bar_label(total_bars, padding=bar_label_padding,
                                    fontsize=bar_label_font_size, rotation=0)

        ax.set_yticks(total_ys)
        # ax.set_ylim(min(total_ys), max(total_ys))
        ax.set_yticklabels(y_tick_labels, fontsize=y_tick_label_font_size)

        ax.yaxis.set_visible(True)
        ax.set_ylabel("Bound", rotation=0, fontsize=axis_label_font_size)
        ax.set_xlabel("# of benchmarks", rotation=0, fontsize=axis_label_font_size)

        ax.spines['bottom'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(True)

        if workload == 'LeetCode':
            ax.set_xticks([0, 5000, 10000, 15000])
            xtick_labels = ['0', '5k', '10k', '15k']
            ax.set_xticklabels(xtick_labels, fontsize=x_tick_label_font_size)
        elif workload == 'Calcite':
            xticks = [0, 50, 100, 150, 200, 250]
            ax.set_xticks(xticks)
            xtick_labels = xticks
            ax.set_xticklabels(xtick_labels, fontsize=x_tick_label_font_size)
        else:
            xticks = [0, 10, 20, 30, 40, 50]
            ax.set_xticks(xticks)
            xtick_labels = xticks
            ax.set_xticklabels(xtick_labels, fontsize=x_tick_label_font_size)

        ax.yaxis.set_label_coords(-0.17, 0.97)
        ax.xaxis.set_label_coords(0.45, 1.13)
        ax.tick_params(axis='x', which='major', pad=5)
        ax.tick_params(axis='y', which='major', pad=5)
        if workload == "LeetCode":
            plt.subplots_adjust(top=.87, bottom=0.02, right=.99, left=0.08)
        else:
            plt.subplots_adjust(top=.87, bottom=0.02, right=.99, left=0.08)

    fig_name = "varying_bound.pdf"
    write_to_figure(fig, "results", fig_name)


def plot_coverage_no_IC():
    # csv schema: tool, workload, unsupported, checked, not checked
    csv_path = "coverage_no_IC.csv"

    leetcode_workload = "LeetCode"
    calcite_workload = "Calcite"
    literature_worklaod = "Literature"

    workloads = [leetcode_workload, calcite_workload, literature_worklaod]

    VeriEQL_tool = "VeriEQL"
    VeriEQL_RQ1_tool = "VeriEQL-RQ1"
    Cosette_tool = "Cosette"
    Qex_tool = "Qex"
    DataFiller_tool = "DataFiller"
    DataFiller_RQ1_tool = "DataFiller-RQ1"
    XData_tool = "XData"
    XData_RQ1_tool = "XData-RQ1"
    SPES_tool = "SPES"
    HoTTSQL_tool = "HoTTSQL"
    # tools = [VeriEQL_RQ1_tool, VeriEQL_tool,
    #          Cosette_tool, Qex_tool, SPES_tool, HoTTSQL_tool]
    TOOLS = [
        [VeriEQL_RQ1_tool, VeriEQL_tool, Cosette_tool, Qex_tool],
        [DataFiller_tool, XData_tool],
        [SPES_tool, HoTTSQL_tool],
    ]

    tool_to_axis_label = {
        VeriEQL_RQ1_tool: "VeriEQL",
        VeriEQL_tool: "VeriEQL-noIC",
        Cosette_tool: "Cosette-noIC",
        Qex_tool: "Qex-noIC",
        DataFiller_RQ1_tool: "DataFiller",
        DataFiller_tool: "DataFiller-noIC",
        XData_RQ1_tool: "XData",
        XData_tool: "XData-noIC",
        SPES_tool: "SPES-noIC",
        HoTTSQL_tool: "HoTTSQL-noIC",
    }

    outcomes = ["unsupported", "checked", "not checked"]
    LABELS = [
        ["unsupported", "checked", "refuted"],
        ["unsupported", "not-refuted", "refuted"],
        ["unsupported", "verified", "not-verified"],
    ]

    # each entry maps (tool, workload, outcome) to the number of benchmarks belonging to this category
    result = {}

    # read in data
    with open(csv_path, 'r') as read_obj:
        next(read_obj)
        csv_reader = reader(read_obj)
        for row in csv_reader:
            # complete this to populate the result
            num_unsupported = float(row[2])
            num_checked = float(row[3])
            num_not_checked = float(row[4])
            total_num = num_unsupported + num_checked + num_not_checked
            percentage_unsupported = round(
                num_unsupported / total_num * 100, 1)
            percentage_checked = round(num_checked / total_num * 100, 1)
            percentage_not_checked = round(
                num_not_checked / total_num * 100, 1)
            result[(row[0], row[1], "unsupported")] = percentage_unsupported
            # result[(row[0], row[1], "unsupported")
            #    ] = round(100 - percentage_checked - percentage_not_checked, 1)
            result[(row[0], row[1], "checked")] = percentage_checked
            result[(row[0], row[1], "not checked")] = percentage_not_checked

    # at this point, result is filled with all necessary data
    # now plot figures
    bar_width = 2
    num_bars_in_group = len(outcomes)
    num_groups = [len(tools) for tools in TOOLS]
    group_width = bar_width * num_bars_in_group
    width_between_groups = 0.5
    left_space = width_between_groups * 0.5
    right_space = left_space
    total_width_per_group = group_width + width_between_groups

    xs = [
        # np.array([i * total_width_per_group for i in range(0, num)])
        np.array([0 for i in range(0, num)])
        for num in num_groups
    ]

    bar_label_font_size = 17
    bar_label_padding = 5
    tick_label_font_size = 20
    axis_label_font_size = 25
    legend_font_size = 20

    group_xs = [x + left_space + group_width / 2 for x in xs]
    unsupported_xs = [x + left_space + bar_width / 2 for x in xs]
    checked_xs = [uxs + bar_width for uxs in unsupported_xs]
    not_checked_xs = [cxs + bar_width for cxs in checked_xs]

    xticks = group_xs
    xtick_labels = [[tool_to_axis_label[tool] for tool in tools] for tools in TOOLS]
    yticks = [0, 20, 40, 60, 80, 100]
    ytick_labels = yticks

    for workload in workloads:

        fig = plt.figure()
        gs = gridspec.GridSpec(
            1,
            sum(num_groups) + len(num_groups) - 1,
        )

        for idx, tools in enumerate(TOOLS):
            for j, tool in enumerate(tools):
                subfigure_idx = j + sum(len(prev_tools) for prev_tools in TOOLS[:idx]) + idx
                ax = fig.add_subplot(gs[0, subfigure_idx])

                # for each tool, map to a list of bar heights
                outcome_to_num_benchmarks = {outcome: [] for outcome in outcomes}
                for outcome in outcomes:
                    num_benchmarks = result[(tool, workload, outcome)]
                    outcome_to_num_benchmarks[outcome].append(num_benchmarks)

                unsupported_bars = ax.bar(
                    x=unsupported_xs[idx][j],
                    height=outcome_to_num_benchmarks["unsupported"][0],
                    width=bar_width,
                    label=LABELS[idx][0],
                    color="white",
                    edgecolor="black",
                    hatch='////',
                )
                # ax.bar_label(unsupported_bars, padding=bar_label_padding,
                #              fontsize=bar_label_font_size)
                for x, y in zip([unsupported_xs[idx][j]], outcome_to_num_benchmarks["unsupported"]):
                    ax.text(
                        x=x,
                        y=y,
                        s=str(y),
                        fontsize=bar_label_font_size,
                        horizontalalignment='center',
                        verticalalignment='bottom',
                    )

                checked_bars = ax.bar(
                    x=checked_xs[idx][j],
                    height=outcome_to_num_benchmarks["checked"][0],
                    width=bar_width,
                    label=LABELS[idx][1],
                    color='white',
                    edgecolor="black",
                )
                # ax.bar_label(checked_bars, padding=bar_label_padding,
                #              fontsize=bar_label_font_size)
                for x, y in zip([checked_xs[idx][j]], outcome_to_num_benchmarks["checked"]):
                    ax.text(
                        x=x,
                        y=y,
                        s=str(y),
                        fontsize=bar_label_font_size,
                        horizontalalignment='center',
                        verticalalignment='bottom',
                    )

                not_checked_bars = ax.bar(
                    x=not_checked_xs[idx][j],
                    height=outcome_to_num_benchmarks["not checked"][0],
                    width=bar_width,
                    label=LABELS[idx][2],
                    color='black',
                    edgecolor="black",
                )
                # ax.bar_label(not_checked_bars, padding=bar_label_padding,
                #              fontsize=bar_label_font_size)
                for x, y in zip([not_checked_xs[idx][j]], outcome_to_num_benchmarks["not checked"]):
                    ax.text(
                        x=x,
                        y=y,
                        s=str(y),
                        fontsize=bar_label_font_size,
                        horizontalalignment='center',
                        verticalalignment='bottom',
                    )

                ax.set_xticks([xticks[idx][j]])
                ax.set_xticklabels([xtick_labels[idx][j]], fontsize=tick_label_font_size)
                # plt.xticks(rotation=30)

                ax.set_yticks(yticks)
                ax.yaxis.set_ticklabels(ytick_labels, fontsize=tick_label_font_size)
                if j == 0:
                    ax.yaxis.set_visible(True)
                else:
                    ax.yaxis.set_visible(False)

                if j == 0:
                    ax.set_ylabel("% of benchmarks", rotation=0,
                                  fontsize=axis_label_font_size)

                ax.set_xlim(0, not_checked_xs[idx][-1] + bar_width / 2 + right_space)
                ax.spines['top'].set_visible(False)
                # ax.spines['bottom'].set_visible(False)
                ax.spines['right'].set_visible(False)
                if j == 0:
                    ax.spines['left'].set_visible(True)
                else:
                    ax.spines['left'].set_visible(False)
                # fig.tight_layout()

                #
                # custom fields
                #
                set_figure_size(fig, 22.5, 2.5)
                ax.yaxis.set_label_coords(0.07, 1.15)
                ax.tick_params(axis='x', which='major', pad=10)
                ax.tick_params(axis='y', which='major', pad=10)
                plt.subplots_adjust(top=.7, bottom=0.15, right=.975, left=0.063)
                if idx == 0 and j == len(TOOLS[idx]) - 1:
                    anchor = (-0.7, 1.55)
                    ax.legend(
                        ncol=3,
                        bbox_to_anchor=anchor,
                        loc='upper center',
                        facecolor='white',
                        framealpha=1,
                        frameon=False,
                        prop={'size': legend_font_size},
                        columnspacing=0.18,
                    )
                if idx == 1 and j == len(TOOLS[idx]) - 1:
                    anchor = (-0.6, 1.55)
                    ax.legend(
                        ncol=3,
                        bbox_to_anchor=anchor,
                        loc='upper center',
                        facecolor='white',
                        framealpha=1,
                        frameon=False,
                        prop={'size': legend_font_size},
                        columnspacing=0.18,
                    )
                if idx == 2 and j == len(TOOLS[idx]) - 1:
                    anchor = (-0.5, 1.55)
                    ax.legend(
                        ncol=3,
                        bbox_to_anchor=anchor,
                        loc='upper center',
                        facecolor='white',
                        framealpha=1,
                        frameon=False,
                        prop={'size': legend_font_size},
                        columnspacing=0.18,
                    )

        fig_name = "coverage_no_IC_" + workload + ".pdf"
        write_to_figure(fig, "results", fig_name)


def plot_coverage():
    # csv schema: tool, workload, unsupported, checked, refuted
    csv_path = "coverage.csv"

    workloads = ["LeetCode", "Calcite", "Literature"]
    # tools = ["Cosette", "Qex", "VeriEQL", "SPES", "HoTTSQL"]
    TOOLS = [["VeriEQL", "Cosette", "Qex"], ["DataFiller", "XData"], ["SPES", "HoTTSQL"]]
    outcomes = ["unsupported", "checked", "refuted"]

    LABELS = [
        ["unsupported", "checked", "refuted"],
        ["unsupported", "not-refuted", "refuted"],
        ["unsupported", "verified", "not-verified"],
    ]

    # each entry maps (tool, workload, outcome) to the number of benchmarks belonging to this category
    result = {}

    # read in data
    with open(csv_path, 'r') as read_obj:
        next(read_obj)
        csv_reader = reader(read_obj)
        for row in csv_reader:
            # complete this to populate the result
            num_unsupported = float(row[2])
            num_checked = float(row[3])
            num_disproved = float(row[4])
            total_num = num_unsupported + num_checked + num_disproved
            percentage_unsupported = round(num_unsupported / total_num * 100, 1)
            percentage_checked = round(num_checked / total_num * 100, 1)
            percentage_not_checked = round(num_disproved / total_num * 100, 1)
            result[(row[0], row[1], "unsupported")] = percentage_unsupported
            # result[(row[0], row[1], "unsupported")
            #    ] = round(100 - percentage_checked - percentage_not_checked, 1)
            result[(row[0], row[1], "checked")] = percentage_checked
            result[(row[0], row[1], "refuted")] = percentage_not_checked

    # at this point, result is filled with all necessary data
    # now plot figures
    bar_width = 2
    num_bars_in_group = len(outcomes)
    num_groups = [len(tools) for tools in TOOLS]
    group_width = bar_width * num_bars_in_group
    width_between_groups = 0.7
    left_space = width_between_groups * 0.5
    right_space = left_space
    total_width_per_group = group_width + width_between_groups

    xs = [
        # np.array([i * total_width_per_group for i in range(0, num)])
        np.array([0 for i in range(0, num)])
        for num in num_groups
    ]

    bar_label_font_size = 18
    bar_label_padding = 5
    tick_label_font_size = 25
    axis_label_font_size = 25
    legend_font_size = 20

    group_xs = [x + left_space + group_width / 2 for x in xs]
    unsupported_xs = [x + left_space + bar_width / 2 for x in xs]
    checked_xs = [uxs + bar_width for uxs in unsupported_xs]
    not_checked_xs = [cxs + bar_width for cxs in checked_xs]

    xticks = group_xs
    xtick_labels = TOOLS
    yticks = [0, 20, 40, 60, 80, 100]
    ytick_labels = yticks

    for workload in workloads:

        fig = plt.figure()
        gs = gridspec.GridSpec(
            1,
            sum(num_groups) + len(num_groups) - 1,
        )

        for idx, tools in enumerate(TOOLS):
            for j, tool in enumerate(tools):
                subfigure_idx = j + sum(len(prev_tools) for prev_tools in TOOLS[:idx]) + idx
                ax = fig.add_subplot(gs[0, subfigure_idx])

                # for each tool, map to a list of bar heights
                outcome_to_num_benchmarks = {outcome: [] for outcome in outcomes}
                for outcome in outcomes:
                    num_benchmarks = result[(tool, workload, outcome)]
                    outcome_to_num_benchmarks[outcome].append(num_benchmarks)

                unsupported_bars = ax.bar(
                    x=unsupported_xs[idx][j],
                    height=outcome_to_num_benchmarks["unsupported"][0],
                    width=bar_width,
                    label=LABELS[idx][0],
                    color="white",
                    edgecolor="black",
                    hatch='////',
                )
                # ax.bar_label(unsupported_bars, padding=bar_label_padding,
                #  fontsize=bar_label_font_size)
                for x, y in zip([unsupported_xs[idx][j]], outcome_to_num_benchmarks["unsupported"]):
                    ax.text(
                        x=x,
                        y=y,
                        s=str(y),
                        fontsize=bar_label_font_size,
                        horizontalalignment='center',
                        verticalalignment='bottom',
                    )

                checked_bars = ax.bar(
                    x=checked_xs[idx][j],
                    height=outcome_to_num_benchmarks["checked"][0],
                    width=bar_width,
                    label=LABELS[idx][1],
                    color='white',
                    edgecolor="black",
                )
                # ax.bar_label(checked_bars, padding=bar_label_padding,
                #              fontsize=bar_label_font_size)
                for x, y in zip([checked_xs[idx][j]], outcome_to_num_benchmarks["checked"]):
                    ax.text(
                        x=x,
                        y=y,
                        s=str(y),
                        fontsize=bar_label_font_size,
                        horizontalalignment='center',
                        verticalalignment='bottom',
                    )

                not_checked_bars = ax.bar(
                    x=not_checked_xs[idx][j],
                    height=outcome_to_num_benchmarks["refuted"][0],
                    width=bar_width,
                    label=LABELS[idx][2],
                    color='black',
                    edgecolor="black",
                )
                # ax.bar_label(not_checked_bars, padding=bar_label_padding,
                #              fontsize=bar_label_font_size)
                for x, y in zip([not_checked_xs[idx][j]], outcome_to_num_benchmarks["refuted"]):
                    ax.text(
                        x=x,
                        y=y,
                        s=str(y),
                        fontsize=bar_label_font_size,
                        horizontalalignment='center',
                        verticalalignment='bottom',
                    )

                ax.set_xticks([xticks[idx][j]])
                ax.set_xticklabels([xtick_labels[idx][j]], fontsize=tick_label_font_size)

                ax.set_yticks(yticks)

                ax.yaxis.set_ticklabels(ytick_labels, fontsize=tick_label_font_size)
                if j == 0:
                    ax.yaxis.set_visible(True)
                else:
                    ax.yaxis.set_visible(False)

                if j == 0:
                    ax.set_ylabel("% of benchmarks", rotation=0, fontsize=axis_label_font_size)

                ax.set_xlim(0, not_checked_xs[idx][-1] + bar_width / 2 + right_space)
                ax.spines['top'].set_visible(False)
                # ax.spines['bottom'].set_visible(False)
                ax.spines['right'].set_visible(False)
                if j == 0:
                    ax.spines['left'].set_visible(True)
                else:
                    ax.spines['left'].set_visible(False)
                # fig.tight_layout()

                #
                # custom fields
                #
                set_figure_size(fig, 21, 2.5)
                ax.yaxis.set_label_coords(0.07, 1.15)
                ax.tick_params(axis='x', which='major', pad=10)
                ax.tick_params(axis='y', which='major', pad=10)
                plt.subplots_adjust(top=.7, bottom=0.15, right=.975, left=0.063)
                if idx == 0 and j == len(TOOLS[idx]) - 1:
                    anchor = (-0.55, 1.55)
                    ax.legend(
                        ncol=3,
                        bbox_to_anchor=anchor,
                        loc='upper center',
                        facecolor='white',
                        framealpha=1,
                        frameon=False,
                        prop={'size': legend_font_size},
                        columnspacing=0.18,
                    )
                if idx == 1 and j == len(TOOLS[idx]) - 1:
                    anchor = (-0.45, 1.55)
                    ax.legend(
                        ncol=3,
                        bbox_to_anchor=anchor,
                        loc='upper center',
                        facecolor='white',
                        framealpha=1,
                        frameon=False,
                        prop={'size': legend_font_size},
                        columnspacing=0.18,
                    )
                if idx == 2 and j == len(TOOLS[idx]) - 1:
                    anchor = (-0.45, 1.55)
                    ax.legend(
                        ncol=3,
                        bbox_to_anchor=anchor,
                        loc='upper center',
                        facecolor='white',
                        framealpha=1,
                        frameon=False,
                        prop={'size': legend_font_size},
                        columnspacing=0.18,
                    )
        fig_name = "coverage_" + workload + ".pdf"
        write_to_figure(fig, "results", fig_name)


def main():
    # RQ1
    plot_coverage()

    # RQ2
    plot_coverage_no_IC()

    # RQ3
    plot_cex()

    # bound distribution
    plot_dist()

    # RQ4
    plot_varying_timeout()
    # plot_varying_bound()
    # plot_operation_performance()


if __name__ == "__main__":
    main()
