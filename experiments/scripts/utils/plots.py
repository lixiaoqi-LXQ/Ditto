import os
import numpy as np

import matplotlib

matplotlib.use("AGG")
import matplotlib.pyplot as plt
from .styles import *


if not os.path.exists("figs"):
    os.mkdir("figs")


def plot_compare_three(
    res_LRU: dict, res_DUMB_R: dict, res_DUMB_S: dict, res_RDMA: dict
):
    LRU, DUMB_R, DUMB_S = 0, 1, 2
    workload_size = 10**7
    real_workload_size = workload_size
    assert res_LRU.keys() == res_DUMB_R.keys()
    cache_sizes = []
    hitrates, tpts = [[[], [], []] for _ in range(2)]
    p50s, p90s, p99s, p999s = [[[], [], []] for _ in range(4)]
    for csize in res_LRU:
        cache_sizes.append(int(csize) * 100 // real_workload_size)
        for eviction, res in zip(
            [LRU, DUMB_R, DUMB_S], [res_LRU, res_DUMB_R, res_DUMB_S]
        ):
            p50s[eviction].append(res[csize]["p50"])
            p90s[eviction].append(res[csize]["p90"])
            p99s[eviction].append(res[csize]["p99"])
            p999s[eviction].append(res[csize]["p999"])
            hitrates[eviction].append(res[csize]["hit-rate-local"])
            tpts[eviction].append(res[csize]["tpt"] / 10**3)
    # latency
    _, ax_lat = plt.subplots()
    for lat_data, name in [
        # (p50s, "p50"),
        (p90s, "p90"),
        # (p99s, "p99"),
        (p999s, "p999"),
    ]:
        ax_lat.plot(cache_sizes, lat_data[LRU], "b-", label="LRU {}".format(name))
        ax_lat.plot(
            cache_sizes,
            lat_data[DUMB_S],
            "g--",
            label="DUMB-S {}".format(name),
        )
        ax_lat.plot(
            cache_sizes,
            lat_data[DUMB_R],
            "k-.",
            label="DUMB-R {}".format(name),
        )

    ax_lat.set_xlabel("Cache size (% workload)")
    ax_lat.set_ylabel("Latency (us)")
    ax_lat.set_xlim(left=cache_sizes[0], right=cache_sizes[-1])
    ax_lat.grid()
    ax_lat.legend(ncol=2)
    plt.savefig(f"figs/latency-three-eviction.png")
    # tpt
    _, ax_tpt = plt.subplots()
    RDMA_tpt_baseline = res_RDMA["tpt"] / 10**3
    ax_tpt.plot(cache_sizes, tpts[LRU], "b-", label="LRU")
    ax_tpt.plot(cache_sizes, tpts[DUMB_S], "g--", label="DUMB-SIMPLE")
    ax_tpt.plot(cache_sizes, tpts[DUMB_R], "k-.", label="DUMB-RANDOM")
    ax_tpt.axhline(RDMA_tpt_baseline, color="lightcoral", linestyle=":", label="RDMA (1x)")
    ax_tpt.axhline(RDMA_tpt_baseline * 2, color="lightcoral", linestyle=":", label="RDMA (2x)")
    ax_tpt.axhline(RDMA_tpt_baseline * 4, color="lightcoral", linestyle=":", label="RDMA (4x)")
    ax_tpt.set_xlabel("Cache size (% workload)")
    ax_tpt.set_ylabel("Throughput (Kops/s)")
    ax_tpt.set_xlim(left=cache_sizes[0], right=cache_sizes[-1])
    ax_tpt.set_ylim(bottom=0)
    ax_tpt.grid()
    ax_tpt.legend(ncol=2)
    plt.savefig(f"figs/tpt-three-eviction.png")

    # hit rate
    _, ax_hit_rate = plt.subplots()
    ax_hit_rate.plot(cache_sizes, hitrates[LRU], "b-", label="LRU")
    ax_hit_rate.plot(cache_sizes, hitrates[DUMB_S], "g--", label="DUMB-SIMPLE")
    ax_hit_rate.plot(cache_sizes, hitrates[DUMB_R], "k-.", label="DUMB-RANDOM")
    ax_hit_rate.set_xlabel("Cache size (% workload)")
    ax_hit_rate.set_xlim(left=cache_sizes[0], right=cache_sizes[-1])
    ax_hit_rate.set_ylabel("Hit Rate")
    # ax_LRU.set_xticks(ticks=[10, 20, 30, 40, 50, 100, 150, 200])
    ax_hit_rate.grid()
    ax_hit_rate.legend()
    plt.savefig(f"figs/hit-rate-three-eviction.png")


def plot_compare_LRU_and_DUMB(res_LRU: dict, res_DUMB: dict, res_RDMA: dict):
    LRU, DUMB = 0, 1
    workload_size = 10**7
    assert res_LRU.keys() == res_DUMB.keys()
    cache_sizes = []
    hitrates, cache_ratios, tpts = [[[], []] for _ in range(3)]
    p50s, p90s, p99s, p999s = [[[], []] for _ in range(4)]
    for csize in res_LRU:
        cache_sizes.append(int(csize) * 100 // workload_size)
        p50s[LRU].append(res_LRU[csize]["p50"])
        p90s[LRU].append(res_LRU[csize]["p90"])
        p99s[LRU].append(res_LRU[csize]["p99"])
        p999s[LRU].append(res_LRU[csize]["p999"])
        p50s[DUMB].append(res_DUMB[csize]["p50"])
        p90s[DUMB].append(res_DUMB[csize]["p90"])
        p99s[DUMB].append(res_DUMB[csize]["p99"])
        p999s[DUMB].append(res_DUMB[csize]["p999"])
        hitrates[LRU].append(res_LRU[csize]["hit-rate-local"])
        hitrates[DUMB].append(res_DUMB[csize]["hit-rate-local"])
        tpts[LRU].append(res_LRU[csize]["tpt"] / 10**3)
        tpts[DUMB].append(res_DUMB[csize]["tpt"] / 10**3)
        # cache_num_key = "local-cache-num(before trans)"
        # if cache_num_key in cache_res[csize]:
        #     cached_num = cache_res[csize][cache_num_key]
        #     cache_ratios.append(cached_num / workload_size)
    # latency
    _, ax_lat = plt.subplots()
    for lat_data, name in [
        (p50s, "p50"),
        (p90s, "p90"),
        (p99s, "p99"),
        (p999s, "p999"),
    ]:
        ax_lat.plot(cache_sizes, lat_data[LRU], label="LRU {}".format(name))
        ax_lat.plot(
            cache_sizes, lat_data[DUMB], linestyle="--", label="DUMB {}".format(name)
        )

    ax_lat.set_xlabel("Cache size (% workload)")
    ax_lat.set_ylabel("Latency (us)")
    # ax_tpt.set_xticks(ticks=[10, 20, 30, 40, 50, 100, 150, 200])
    ax_lat.set_xlim(left=cache_sizes[0], right=cache_sizes[-1])
    # ax_tpt.set_ylim(bottom=0)
    ax_lat.grid()
    ax_lat.legend(ncol=2)
    plt.savefig(f"figs/latency-LRU&DUMB.png")

    # tpt
    _, ax_tpt = plt.subplots()
    ax_tpt.plot(cache_sizes, tpts[LRU], "b-", label="LRU")
    ax_tpt.plot(cache_sizes, tpts[DUMB], "g--", label="DUMB")
    ax_tpt.axhline(res_RDMA["tpt"] / 10**3, color="r", linestyle=":", label="RDMA")
    ax_tpt.set_xlabel("Cache size (% workload)")
    ax_tpt.set_ylabel("Throughput (Kops/s)")
    # ax_tpt.set_xticks(ticks=[10, 20, 30, 40, 50, 100, 150, 200])
    ax_tpt.set_xlim(left=cache_sizes[0], right=cache_sizes[-1])
    ax_tpt.set_ylim(bottom=0)
    ax_tpt.grid()
    ax_tpt.legend()
    plt.savefig(f"figs/tpt-LRU&DUMB.png")

    # hit rate
    _, ax_hit_rate = plt.subplots()
    ax_hit_rate.plot(cache_sizes, hitrates[LRU], "b-", label="LRU")
    ax_hit_rate.plot(cache_sizes, hitrates[DUMB], "g--", label="DUMB")
    ax_hit_rate.set_xlabel("Cache size (% workload)")
    ax_hit_rate.set_xlim(left=cache_sizes[0], right=cache_sizes[-1])
    ax_hit_rate.set_ylabel("Hit Rate")
    # ax_LRU.set_xticks(ticks=[10, 20, 30, 40, 50, 100, 150, 200])
    ax_hit_rate.grid()
    ax_hit_rate.legend()
    plt.savefig(f"figs/hit-rate-LRU&DUMB.png")


def plot_cache_size_matrices(res_cache: dict, res_RDMA: dict, topic: str):
    workload_size = 10**7
    hitrates, cache_ratios, tpts, cache_sizes = [[] for _ in range(4)]
    p50s, p90s, p99s, p999s = [[] for _ in range(4)]
    for csize in res_cache:
        cache_sizes.append(int(csize) * 100 // workload_size)
        p50s.append(res_cache[csize]["p50"])
        p90s.append(res_cache[csize]["p90"])
        p99s.append(res_cache[csize]["p99"])
        p999s.append(res_cache[csize]["p999"])
        hitrates.append(res_cache[csize]["hit-rate-local"])
        tpts.append(res_cache[csize]["tpt"] / 10**3)
        cache_num_key = "local-cache-num(before trans)"
        if cache_num_key in res_cache[csize]:
            cached_num = res_cache[csize][cache_num_key]
            cache_ratios.append(cached_num / workload_size)

    # tpt
    _, ax_tpt = plt.subplots()
    ax_tpt.plot(cache_sizes, tpts, marker=".")
    ax_tpt.axhline(res_RDMA["tpt"] / 10**3, linestyle="--", color="r")
    ax_tpt.set_xlabel("Cache size (% workload)", fontsize=16)
    ax_tpt.set_ylabel("Throughput (Kops/s)", fontsize=16)
    # ax_tpt.set_xticks(ticks=[10, 20, 30, 40, 50, 100, 150, 200])
    ax_tpt.set_xlim(left=cache_sizes[0], right=cache_sizes[-1])
    ax_tpt.set_ylim(bottom=0)
    ax_tpt.grid()
    ax_tpt.legend(["Ditto+", "Ditto"])
    plt.savefig(f"figs/tpt-{topic}.png")

    # p99
    _, ax_lat = plt.subplots()
    ax_lat.plot(cache_sizes, p50s, "*--", color="#0097A7", label="p50 Ditto+")
    ax_lat.plot(cache_sizes, p90s, ".-", color="#0097A7", label="p90 Ditto+")
    ax_lat.plot(cache_sizes, p99s, ".--", color="#1976D2", label="p99 Ditto+")
    ax_lat.plot(cache_sizes, p999s, ".-", color="#1976D2", label="p999 Ditto+")
    ax_lat.axhline(res_RDMA["p99"], linestyle="--", color="#F44336", label="p99 Ditto")
    ax_lat.axhline(res_RDMA["p50"], linestyle="-.", color="#E57373", label="p50 Ditto")
    ax_lat.set_xlabel("Cache size (% workload)", fontsize=16)
    ax_lat.set_ylabel("Lantency (us)", fontsize=16)
    ax_lat.set_xticks(ticks=[10, 20, 30, 40, 50, 100, 150, 200])
    ax_lat.set_xlim(left=cache_sizes[0], right=cache_sizes[-1])
    ax_lat.grid()
    ax_lat.legend(ncol=3)
    plt.savefig(f"figs/latency-{topic}.png")

    # hit rate
    _, ax_hitrate = plt.subplots()
    (line,) = ax_hitrate.plot(cache_sizes, hitrates, ".-", label="hit-rate")
    ax_hitrate.set_xlabel("Cache size (% workload)", fontsize=16)
    ax_hitrate.set_xlim(left=cache_sizes[0], right=cache_sizes[-1])
    ax_hitrate.set_ylabel("Hit Rate", fontsize=16)
    # ax_hitrate.set_xticks(ticks=[10, 20, 30, 40, 50, 100, 150, 200])
    ax_hitrate.grid()
    if len(cache_ratios) != 0:
        ax_cacheratio = ax_hitrate.twinx()
        ax_cacheratio.set_ylim(0, 1)
        fill = ax_cacheratio.fill_between(
            cache_sizes,
            cache_ratios,
            0,
            color="#0D47A1",
            alpha=0.1,
            label="cache-ratio",
        )
        ax_cacheratio.set_ylabel("Cache Ratio", fontsize=16)
        ax_cacheratio.set_yticks(ticks=[0.0, 0.1, 0.2, 0.3, 0.5, 1])
        ax_cacheratio.legend(loc="center right", handles=[line, fill])
    plt.savefig(f"figs/hit-rate-{topic}.png")


def plot_fig1(res: dict):
    _, ax_L = plt.subplots(1, 1, figsize=(7, 2.5), dpi=300)
    ax_R = ax_L.twinx()
    avg = 8
    tpt = res["tpt"][1:-1]
    y_tpt = []
    x_tpt = []
    for i in range(0, len(tpt), avg):
        w = avg
        if i + avg >= len(tpt):
            w = len(tpt) - i
        x_tpt.append(i / 2)
        tmp = np.average([tpt[i + p] for p in range(w)])
        y_tpt.append(tmp / 1000000)
    ax_L.plot(x_tpt, y_tpt, color=lineColorDict["cliquemap-precise-lru"], linewidth=0.8)

    x_p99 = [i * 4 for i in range(len(res["p99_cont"]))]
    y_p99 = np.array(res["p99_cont"]) / 100
    ax_R.plot(
        x_p99[1:],
        y_p99[1:],
        color=lineColorDict["sample-adaptive"],
        linewidth=0.8,
        label="p99",
        linestyle="--",
    )

    # plot x line
    plt.axvline(
        res["rebalance_start_time"], color="grey", linestyle="--", linewidth=0.5
    )
    ax_L.plot(
        [res["rebalance_end_time"]] * 2,
        [0, 3.6],
        color="grey",
        linestyle="--",
        linewidth=0.5,
    )
    ax_L.plot(
        [res["shrink_start_time"]] * 2,
        [0, 3.6],
        color="grey",
        linestyle="--",
        linewidth=0.5,
    )
    plt.axvline(
        res["shrink_start_time"] + res["shrink_period_1"],
        color="grey",
        linestyle="--",
        linewidth=0.5,
    )

    # annotate rebalance
    ax_L.annotate(
        "",
        xy=(175, 2.5),
        xytext=(493, 2.5),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.8),
    )
    ax_L.text(190, 2.35, "rebalance data", fontsize=14)

    # annotate shrink
    ax_L.annotate(
        "",
        xy=(664, 2.5),
        xytext=(1008, 2.5),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.8),
    )
    ax_L.text(715, 2.35, "reshard data", fontsize=14)

    # annotate number of cores
    ax_L.text(0, 3.75, "32 nodes", fontsize=14)
    ax_L.annotate(
        "",
        xy=(0, 3.7),
        xytext=(185, 3.7),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.8),
    )
    ax_L.text(490, 3.75, "64 nodes", fontsize=14)
    ax_L.annotate(
        "",
        xy=(175, 3.7),
        xytext=(1008, 3.7),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.8),
    )
    ax_L.text(1015, 3.75, "32 nodes", fontsize=14)
    ax_L.annotate(
        "",
        xy=(995, 3.7),
        xytext=(1210, 3.7),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.8),
    )

    ax_L.grid(axis="y", linewidth=0.3)
    ax_L.set_xlim(-2, 1210)
    ax_L.set_ylim(2.3, 3.9)
    ax_L.set_yticks([2.3, 2.5, 2.7, 2.9, 3.1, 3.3, 3.5, 3.7, 3.9])
    ax_R.set_ylim(0.2, 2)
    ax_R.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8])
    ax_L.set_xlabel("Time (seconds)", fontsize=16)
    ax_L.set_ylabel("Throughput (Mops/s)", fontsize=15)
    ax_R.set_ylabel("p99 Latency (ms)", fontsize=15)
    ax_L.tick_params(labelsize=14)
    ax_R.tick_params(labelsize=14)
    ax_L.legend(
        ["Throughput"],
        bbox_to_anchor=(0.35, 1.21),
        frameon=False,
        fontsize=15,
        handletextpad=0.3,
    )
    ax_R.legend(
        ["p99"],
        bbox_to_anchor=(0.55, 1.21),
        frameon=False,
        fontsize=15,
        handletextpad=0.3,
    )
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig1.pdf", bbox_inches="tight")


def _subplot_bar_fig2(res, workload_list, method_list):
    _, ax_L = plt.subplots(1, 1, figsize=(4, 2.1), dpi=300)
    ax_R = ax_L.twinx()
    xList = np.arange(len(workload_list))
    totalWidth = 0.6
    width = totalWidth / len(method_list)
    barwidth = width * 0.8
    for i, m in enumerate(method_list):
        ax_L.bar(
            [xList[0] + i * width],
            res[m]["tpt"][0] / 1000,
            width=barwidth,
            label=methodLabelDict[m],
            edgecolor="black",
            fill=True,
            color=barColorDict[m],
            linewidth=0.2,
            hatch=barHatchDict[m],
            zorder=100,
        )
        ax_R.bar(
            [xList[1] + i * width],
            res[m]["p99"][0],
            width=barwidth,
            edgecolor="black",
            fill=True,
            color=barColorDict[m],
            linewidth=0.2,
            hatch=barHatchDict[m],
        )
        ax_R.bar(
            [xList[2] + i * width],
            res[m]["p50"],
            width=barwidth,
            edgecolor="black",
            fill=True,
            color=barColorDict[m],
            linewidth=0.2,
            hatch=barHatchDict[m],
        )
    ax_L.set_ylabel("Throughput (Kops/s)", fontsize=16)
    # ax_L.set_xlabel('Metrics', fontsize=16)
    ax_L.set_xlabel(" ", fontsize=12)
    ax_R.set_ylabel("Latency (us)", fontsize=16)
    ax_R.set_ylim(0, 70)
    ax_R.set_yticks([0, 20, 40, 60])
    ax_L.set_xticks([0.2, 1.2, 2.2])
    ax_L.set_xticklabels(["Throughput", "P50", "P99"], fontsize=16)
    ax_L.set_ylim(0, 140)
    ax_L.set_yticks([0, 40, 80, 120])
    ax_L.tick_params(labelsize=17)
    ax_R.tick_params(labelsize=17)
    ax_L.legend(
        fontsize=16,
        frameon=False,
        ncol=3,
        handletextpad=0.2,
        columnspacing=1,
        bbox_to_anchor=(1.15, 1.27),
    )
    ax_L.grid(axis="y", zorder=0)
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig2_a.pdf", format="pdf", bbox_inches="tight")


def _subplot_line_fig2(res_dict, method_list):
    _, ax = plt.subplots(1, 1, figsize=(4, 2), dpi=300)
    for i, m in enumerate(method_list):
        y = np.array(res_dict[m]["tpt"]) / 1000
        x = [i for i in range(len(y))]
        ax.plot(
            x,
            y,
            linestyle=lineStyleDict[m],
            color=lineColorDict[m],
            marker=lineMarkerDict[m],
            markerfacecolor="none",
            label=methodLabelDict[m],
            linewidth=1,
        )
    ax.set_ylabel("Throughput (Kops/s)", fontsize=16)
    ax.set_xlabel("Number of Clients", fontsize=17)
    ax.set_yscale("log")
    ax.set_ylim(0.1, 600000)
    ax.set_yticks([1, 100, 10000])
    ax.set_xticks([i for i in range(10)])
    ax.set_xticklabels(
        ["1", "2", "4", "8", "16", "32", "64", "96", "128", "160"], fontsize=12
    )
    ax.tick_params(labelsize=14)
    ax.grid()
    ax.legend(
        fontsize=16,
        bbox_to_anchor=(1.06, 1.27),
        frameon=False,
        handletextpad=0.2,
        ncol=3,
        columnspacing=0.5,
    )
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig2_b.pdf", format="pdf", bbox_inches="tight")


def plot_fig2(res: dict):
    workload_list = ["tpt", "p50", "p99"]
    method_list = ["non", "shard-lru", "precise-lru"]
    client_num_list = [1, 2, 4, 8, 16, 32, 64, 96, 128, 160]
    policy_data = {}
    for m in method_list:
        policy_data[m] = {}
        tpt_list = []
        lat_list = []
        for c in client_num_list:
            tpt_list.append(res[m][f"{c}"]["tpt"])
            lat_list.append(res[m][f"{c}"]["p99"])
        policy_data[m]["tpt"] = tpt_list
        policy_data[m]["p99"] = lat_list
    policy_data["non"]["p50"] = res["non"]["1"]["p50"]
    policy_data["shard-lru"]["p50"] = res["shard-lru"]["1"]["p50"]
    policy_data["precise-lru"]["p50"] = res["precise-lru"]["1"]["p50"]

    barHatchDict["precise-lru"] = "//"
    barColorDict["precise-lru"] = barColorDict["precise-lru"]
    methodLabelDict["precise-lru"] = "KVC"
    barHatchDict["shard-lru"] = "xx"
    barColorDict["shard-lru"] = barColorDict["cliquemap-precise-lru"]
    methodLabelDict["shard-lru"] = "KVC-S"
    _subplot_bar_fig2(policy_data, workload_list, method_list)

    lineColorDict["precise-lru"] = "#0066cc"
    lineStyleDict["precise-lru"] = lineStyleDict["precise-lru"]
    lineMarkerDict["precise-lru"] = lineMarkerDict["precise-lru"]
    lineColorDict["shard-lru"] = lineColorDict["cliquemap-precise-lfu"]
    lineStyleDict["shard-lru"] = lineStyleDict["cliquemap-precise-lfu"]
    lineMarkerDict["shard-lru"] = lineMarkerDict["cliquemap-precise-lfu"]
    _subplot_line_fig2(policy_data, method_list)


def plot_fig13(redis_result: dict, ela_cpu_result: dict, ela_mem_result: dict):
    data = {
        "redis": redis_result,
        "sample-adaptive-cpu": ela_cpu_result,
        "sample-adaptive-mem": ela_mem_result,
    }
    method_list = ["redis", "sample-adaptive-cpu", "sample-adaptive-mem"]

    fig, ax = plt.subplots(3, 1, figsize=(7, 4), dpi=300, sharex=True)

    avg = 8
    for k in range(len(method_list)):
        m = method_list[k]
        tpt = data[m]["tpt"][1:-1]
        y = []
        x = []
        for i in range(0, len(tpt), avg):
            w = avg
            if i + avg >= len(tpt):
                w = len(tpt) - i
            x.append(i / 2)
            tmp = np.average([tpt[i + p] for p in range(w)])
            y.append(tmp / 1000000)
        if m == "redis":
            style = (0, (5, 1))
        else:
            style = lineStyleDict[m]
        ax[k].plot(
            x,
            y,
            color=lineColorDict[m],
            linestyle=style,
            linewidth=1,
            label=methodLabelDict[m],
        )

    # plot x line
    ax[0].plot(
        [data["redis"]["rebalance_end_time"]] * 2,
        [0, 3.6],
        color="grey",
        linestyle="--",
        linewidth=0.5,
    )
    ax[0].axvline(
        data["redis"]["shrink_start_time"] + data["redis"]["shrink_period_1"],
        color="grey",
        linestyle="--",
        linewidth=0.5,
    )

    # annotate rebalance
    ax[0].annotate(
        "",
        xy=(175, 2.4),
        xytext=(493, 2.4),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[0].text(220, 1.9, "Rebalance data", fontsize=10)
    # annotate shrink
    ax[0].annotate(
        "",
        xy=(664, 2.4),
        xytext=(1008, 2.4),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[0].text(740, 1.9, "Reshard data", fontsize=10)

    # annotate number of cores
    ax[1].text(38, 7.1, "32 cores", fontsize=10)
    ax[1].text(53, 6.3, "on CN", fontsize=10)
    ax[1].annotate(
        "",
        xy=(0, 6.1),
        xytext=(180, 6.1),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[1].text(350, 7.1, "64 cores", fontsize=10)
    ax[1].text(365, 6.3, "on CN", fontsize=10)
    ax[1].annotate(
        "",
        xy=(175, 6.1),
        xytext=(670, 6.1),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[1].text(865, 7.1, "32 cores", fontsize=10)
    ax[1].text(880, 6.3, "on CN", fontsize=10)
    ax[1].annotate(
        "",
        xy=(665, 6.1),
        xytext=(1210, 6.1),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[0].text(38, 4.5, "32 cores", fontsize=10)
    ax[0].text(0, 4.0, "32GB DRAM", fontsize=10)
    ax[0].annotate(
        "",
        xy=(0, 3.8),
        xytext=(180, 3.8),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[0].text(500, 4.5, "64 cores", fontsize=10)
    ax[0].text(470, 4.0, "64GB DRAM", fontsize=10)
    ax[0].annotate(
        "",
        xy=(175, 3.8),
        xytext=(1005, 3.8),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[0].text(1050, 4.5, "32 cores", fontsize=10)
    ax[0].text(1010, 4.0, "32GB DRAM", fontsize=10)
    ax[0].annotate(
        "",
        xy=(1000, 3.8),
        xytext=(1210, 3.8),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[2].text(0, 7.2, "32GB DRAM", fontsize=10)
    ax[2].text(48, 6.3, "on MN", fontsize=10)
    ax[2].annotate(
        "",
        xy=(0, 6.1),
        xytext=(180, 6.1),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[2].text(330, 7.2, "64GB DRAM", fontsize=10)
    ax[2].text(380, 6.3, "on MN", fontsize=10)
    ax[2].annotate(
        "",
        xy=(175, 6.1),
        xytext=(670, 6.1),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )
    ax[2].text(845, 7.2, "32GB DRAM", fontsize=10)
    ax[2].text(895, 6.3, "on MN", fontsize=10)
    ax[2].annotate(
        "",
        xy=(665, 6.1),
        xytext=(1210, 6.1),
        arrowprops=dict(arrowstyle="<->", color="black", linewidth=0.5),
    )

    ax[2].set_xlim(-1, 1210)

    ax[1].grid(axis="y", linewidth=0.3)
    ax[1].set_ylim(4, 10)
    ax[1].set_yticks([4 + i * 1.5 for i in range(5)])
    ax[1].set_yticklabels(["4.0", "5.5", "7.0", "8.5", "10.0"])
    ax[0].grid(axis="y", linewidth=0.3)
    ax[0].set_ylim(1.8, 5.0)
    ax[0].set_yticks([1.8 + i * 0.8 for i in range(5)])
    ax[0].set_yticklabels(["1.8", "2.6", "3.4", "4.2", "5.0"])
    ax[2].grid(axis="y", linewidth=0.3)
    ax[2].set_ylim(3, 9)
    ax[2].set_yticks([2 + i * 1.5 for i in range(5)])
    ax[2].set_yticklabels(["2.0", "3.5", "5.0", "6.5", "8.0"])

    ax[1].set_ylabel("Throughput (Mops/s)", fontsize=14)
    ax[2].set_xlabel("Time (seconds)", fontsize=14)

    ax[0].tick_params(labelsize=12)
    ax[1].tick_params(labelsize=12)
    ax[2].tick_params(labelsize=12)
    ax[0].tick_params(labelsize=12, axis="x", which="both", bottom=False)
    ax[1].tick_params(labelsize=12, axis="x", which="both", bottom=False)
    ax[0].legend(
        fontsize=12, bbox_to_anchor=(0.185, 1.35), frameon=False, handletextpad=0.5
    )
    ax[1].legend(
        fontsize=12, bbox_to_anchor=(0.53, 2.55), frameon=False, handletextpad=0.5
    )
    ax[2].legend(
        fontsize=12, bbox_to_anchor=(0.92, 3.75), frameon=False, handletextpad=0.5
    )
    ax[1].spines["top"].set_visible(False)
    ax[0].spines["top"].set_visible(False)
    ax[2].spines["top"].set_visible(False)
    ax[1].spines["right"].set_visible(False)
    ax[0].spines["right"].set_visible(False)
    ax[2].spines["right"].set_visible(False)

    # plot meta lines
    meta_ax = fig.add_subplot(111, facecolor="none")
    meta_ax.tick_params(
        axis="both",
        which="both",
        left=False,
        bottom=False,
        labelleft=False,
        labelbottom=False,
    )
    for _, spine in meta_ax.spines.items():
        spine.set_visible(False)
    meta_ax.get_shared_x_axes().join(meta_ax, ax[0])
    meta_ax.get_shared_y_axes().join(meta_ax, ax[0])
    meta_ax.axvline(0.1485, color="gray", linewidth=0.5, linestyle="--")
    meta_ax.plot([0.553, 0.553], [0, 0.87], color="gray", linewidth=0.5, linestyle="--")

    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig13.pdf", bbox_inches="tight")


def _subplot_fig14(res_dict: dict, method_list, figName, show_label=False):
    _, ax = plt.subplots(1, 1, figsize=(4, 1.7), dpi=300)
    for i, m in enumerate(method_list):
        x = np.array(res_dict[m]["x"]) / 1000000
        y = np.array(res_dict[m]["y"])
        ax.plot(
            x,
            y,
            linestyle=lineStyleDict[m],
            color=lineColorDict[m],
            marker=lineMarkerDict[m],
            markerfacecolor="none",
            label=methodLabelDict[m],
            linewidth=1,
        )
    ax.set_xlabel("Throughput (Mops/s)", fontsize=16)
    ax.set_xscale("log")
    ax.set_xlim(0.05, 15)
    ax.set_xticks([0.1, 0.3, 1, 3, 10])
    ax.set_xticklabels([0.1, 0.3, 1, 3, 10])
    ax.set_ylabel("p99 Latency (us)", fontsize=15)
    ax.set_yscale("log")
    ax.set_ylim(10, 10000)
    ax.set_yticks([10 ** (i / 2) for i in range(2, 9)])
    ax.tick_params(labelsize=14)
    ax.grid(linewidth=0.3)
    if show_label:
        ax.legend(fontsize=13, loc="upper right", frameon=False, labelspacing=0.2)
    figName = "figs/" + figName
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig(f"{figName}.pdf", format="pdf", bbox_inches="tight")


def plot_fig14(res: dict):
    method_list = [
        "cliquemap-precise-lru",
        "cliquemap-precise-lfu",
        "sample-adaptive",
        "shard-lru",
    ]
    workload_list = ["ycsba", "ycsbb", "ycsbc", "ycsbd"]
    caption_list = ["a", "b", "c", "d"]
    client_num_list = [1, 2, 4, 8, 16, 32, 64, 96, 128, 192, 224, 256]
    ycsb_data = {}
    for wl in workload_list:
        ycsb_data[wl] = {}
        for m in method_list:
            ycsb_data[wl][m] = {}
            tpt_list = []
            lat_list = []
            for c in client_num_list:
                tpt_list.append(res[wl][m][f"{c}"]["tpt"])
                lat_list.append(res[wl][m][f"{c}"]["p99"])
            ycsb_data[wl][m]["x"] = tpt_list
            ycsb_data[wl][m]["y"] = lat_list

    for i, wl in enumerate(workload_list):
        use_caption = True if i == 0 else False
        _subplot_fig14(
            ycsb_data[wl], method_list, f"fig14_{caption_list[i]}", use_caption
        )


def _subplot_fig15_16(res_dict, method_list, op, figName, show_label=False, ylim=None):
    _, ax = plt.subplots(1, 1, figsize=(3, 2), dpi=300)
    x = [0, 1, 2, 3]
    for i, m in enumerate(method_list):
        y = np.array(res_dict[m][op])
        if op == "tpt":
            y /= 1000
        ax.plot(
            x,
            y,
            linestyle=lineStyleDict[m],
            color=lineColorDict[m],
            marker=lineMarkerDict[m],
            markerfacecolor="none",
            label=methodLabelDict[m],
            linewidth=1.5,
        )
    if op == "tpt":
        ax.set_ylabel("Throughput (Kops/s)")
    else:
        ax.set_ylabel("Hit Rate")
    if ylim != None:
        ax.set_ylim(ylim)
    ax.set_xlabel("Cache Size (% Trace Footprint)")
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["1", "5", "10", "20"])
    ax.tick_params(labelsize=14)
    ax.grid(linewidth=0.3)
    if show_label:
        if op == "hr":
            # ax.set_ylim(0.3, 1.2)
            ax.set_yticks([0.4, 0.6, 0.8, 1.0])
        else:
            # ax.set_ylim(150, 510)
            ax.set_yticks([200, 300, 400])
        ax.legend(frameon=False, labelspacing=0.05, handletextpad=0.3)
    if not os.path.exists("figs"):
        os.mkdir("figs")
    figName = "figs/" + figName + ".pdf"
    plt.savefig(figName, format="pdf", bbox_inches="tight")


def plot_fig15_16(result: dict):
    workload_list = [
        # "webmail-all",
        "twitter020-10m",
        # "twitter049-10m",
        # "twitter042-10m",
        # "ibm044-10m",
    ]
    method_list = [
        # "cliquemap-precise-lru",
        # "cliquemap-precise-lfu",
        # "sample-lru",
        # "sample-lfu",
        "sample-adaptive",
    ]
    cache_size_list = ["0.01", "0.05", "0.1", "0.2"]

    workload_data = {}
    for wl in workload_list:
        workload_data[wl] = {}
        for m in method_list:
            workload_data[wl][m] = {}
            tpt_list = []
            hr_list = []
            for cache_sz in cache_size_list:
                tpt_list.append(result[wl][m][cache_sz]["tpt"])
                hr_list.append(result[wl][m][cache_sz]["hr"])
            workload_data[wl][m]["tpt"] = tpt_list
            workload_data[wl][m]["hr"] = hr_list

    idx_list = ["a", "b", "c", "d", "e"]
    for i, wl in enumerate(workload_list):
        show_label = False
        ylim = None
        if i == 0:
            show_label = True
            ylim = (0.3, 1)
        _subplot_fig15_16(
            workload_data[wl], method_list, "tpt", f"fig15_{idx_list[i]}", show_label
        )
        _subplot_fig15_16(
            workload_data[wl],
            method_list,
            "hr",
            f"fig16_{idx_list[i]}",
            show_label,
            ylim,
        )


def _subplot_fig17(res_dict, method_list, workload, figName):
    fig, ax = plt.subplots(1, 1, figsize=(4, 1.7), dpi=300)
    for i, m in enumerate(method_list):
        tpt = np.array(res_dict[m]) / 1000000
        if m == "redis":
            ax.plot(
                tpt,
                linestyle=lineStyleDict["sample-lru"],
                color=lineColorDict["sample-lru"],
                marker=lineMarkerDict["sample-lru"],
                markerfacecolor="none",
                label="Redis",
                linewidth=1,
            )
        else:
            ax.plot(
                tpt,
                linestyle=lineStyleDict[m],
                color=lineColorDict[m],
                marker=lineMarkerDict[m],
                markerfacecolor="none",
                label=methodLabelDict[m],
                linewidth=1,
            )
    ax.set_ylabel("Throughput (Mops/s)", fontsize=15)
    ax.set_xlabel("Number of CPU cores", fontsize=16)
    ax.set_xticks([i for i in range(14)])
    ax.set_xticklabels(
        ["1", "2", "4", "8", "12", "16", "20", "24", "28", "32", "36", "40", "44", "48"]
    )
    ax.tick_params(labelsize=14)
    if "ycsba" in workload:
        ax.set_ylim(0, 14)
        ax.set_yticks([0, 2, 4, 6, 8, 10, 12, 14])
    else:
        ax.set_ylim(0, 14)
        ax.set_yticks([0, 2, 4, 6, 8, 10, 12, 14])
    ax.tick_params(labelsize=12)
    ax.grid(linewidth=0.5)
    ax.legend(
        fontsize=14,
        bbox_to_anchor=(0.84, 1.45),
        frameon=False,
        labelspacing=0.1,
        ncol=2,
        columnspacing=1,
        handletextpad=0.5,
    )
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig(f"figs/{figName}", format="pdf", bbox_inches="tight")


def plot_fig17(result: dict, ada_res: dict):
    method_list = ["cliquemap-shard-lru", "cliquemap-shard-lfu", "redis"]
    workload_list = ["ycsba", "ycsbc"]
    client_num_list = [1, 2, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48]
    data = {}
    for wl in workload_list:
        data[wl] = {}
        for m in method_list:
            data[wl][m] = []
            for c in client_num_list:
                data[wl][m].append(result[wl][m][f"{c}"]["tpt"])
    # load sample-adaptive data
    for wl in workload_list:
        data[wl]["sample-adaptive"] = [
            ada_res[wl]["sample-adaptive"]["256"]["tpt"]
        ] * len(client_num_list)

    id_list = ["a", "b"]
    method_list.append("sample-adaptive")
    for i, wl in enumerate(workload_list):
        _subplot_fig17(data[wl], method_list, wl, f"fig17_{id_list[i]}.pdf")


def plot_fig18(result: dict):
    wl_list = ["0.01", "0.1"]
    method_list = ["sample-lru", "sample-lfu", "sample-adaptive", "non"]
    key_list = list(result.keys())
    data = {}
    for wl in wl_list:
        tmp_res = {}
        for m in method_list:
            res_list = []
            for k in key_list:
                res_list.append(result[k][m][wl]["hr"])
            tmp_res[m] = res_list
        data[wl] = tmp_res

    plot_data = {}
    for wl in wl_list:
        plot_data[wl] = {}
        max_list = []
        min_list = []
        cur_res = data[wl]
        for i in range(len(cur_res["sample-lru"])):
            max_list.append(max(cur_res["sample-lru"][i], cur_res["sample-lfu"][i]))
            min_list.append(min(cur_res["sample-lru"][i], cur_res["sample-lfu"][i]))
        plot_data[wl]["max"] = np.array(max_list) / np.array(cur_res["non"])
        plot_data[wl]["min"] = np.array(min_list) / np.array(cur_res["non"])
        plot_data[wl]["sample-adaptive"] = np.array(
            cur_res["sample-adaptive"]
        ) / np.array(cur_res["non"])

    plot_data_list = [
        plot_data["0.01"]["min"],
        plot_data["0.01"]["sample-adaptive"],
        plot_data["0.01"]["max"],
        plot_data["0.1"]["min"],
        plot_data["0.1"]["sample-adaptive"],
        plot_data["0.1"]["max"],
    ]

    _, ax = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    ax.boxplot(plot_data_list, showfliers=False)

    ax.axvline(x=3.5, color="black", linestyle="--", linewidth=0.8)
    ax.text(0.6, 1.3, "1% trace size", fontsize=16)
    ax.text(3.6, 1.3, "10% trace size", fontsize=16)

    ax.set_xticklabels(["Min", "Ditto", "Max", "Min", "Ditto", "Max"])
    ax.set_ylim(0.6, 1.4)
    ax.tick_params(labelsize=16, axis="x")
    ax.tick_params(labelsize=15, axis="y")
    ax.set_ylabel("Relative Hit Rate", fontsize=16)
    ax.grid(linewidth=0.3)

    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig18.pdf", bbox_inches="tight")


def plot_fig19(res: dict):
    workload_list = ["tpt", "hr"]
    method_list = [
        "cliquemap-precise-lru",
        "cliquemap-precise-lfu",
        "sample-lru",
        "sample-lfu",
        "sample-adaptive",
    ]
    fig, ax_L = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    ax_R = ax_L.twinx()
    xList = np.arange(len(workload_list))
    totalWidth = 0.8
    width = totalWidth / len(method_list)
    for i, m in enumerate(method_list):
        ax_L.bar(
            [xList[0] + (i - 1) * width],
            res[m]["tpt"] / 1000,
            width=width,
            label=methodLabelDict[m],
            edgecolor="black",
            fill=True,
            color=barColorDict[m],
            linewidth=0.2,
            hatch=barHatchDict[m],
            zorder=100,
        )
        ax_R.bar(
            [xList[1] + (i - 1) * width],
            res[m]["hr"],
            width=width,
            edgecolor="black",
            fill=True,
            color=barColorDict[m],
            linewidth=0.2,
            hatch=barHatchDict[m],
            zorder=100,
        )
    ax_L.set_xticks([0.16, 1.16])
    ax_L.set_xticklabels(["Throughput", "Hit Rate"])
    # ax_L.set_xlabel('   ', fontsize=16)
    ax_L.set_ylabel("Throughput (Kops/s)", fontsize=16)
    ax_L.set_ylim(0, 1000)
    ax_L.set_yticks([0, 300, 600, 900])
    ax_R.set_ylabel("Hit Rate", fontsize=16)
    ax_R.set_ylim(0.5, 1.0)
    ax_L.legend(
        fontsize=14,
        frameon=False,
        ncol=2,
        handletextpad=0.3,
        labelspacing=0.2,
        columnspacing=0.4,
        bbox_to_anchor=(1.02, 1.06),
    )
    ax_L.tick_params(labelsize=16, axis="x")
    ax_L.tick_params(labelsize=15, axis="y")
    ax_R.tick_params(labelsize=16, axis="x")
    ax_R.tick_params(labelsize=15, axis="y")
    ax_L.grid(zorder=0, linewidth=0.3)
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig19.pdf", format="pdf", bbox_inches="tight")


def plot_fig20(res: dict):
    method_list = [
        "sample-lru",
        "sample-lfu",
        "sample-adaptive",
        "cliquemap-precise-lru",
        "cliquemap-precise-lfu",
    ]
    mix_data = {}
    for m in method_list:
        mix_data[m] = {}
        mix_data[m]["hr"] = []
        for i in range(0, 11):
            k = f"r{i}-f{10-i}"
            mix_data[m]["hr"].append(res[m][k]["hr"])

    _, ax = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    base = np.array(mix_data["sample-lru"]["hr"])
    for i, m in enumerate(method_list):
        y = np.array(mix_data[m]["hr"]) / base
        x = [i / 10 for i in range(len(y))]
        ax.plot(
            x,
            y,
            linestyle=lineStyleDict[m],
            color=lineColorDict[m],
            marker=lineMarkerDict[m],
            markerfacecolor="none",
            label=methodLabelDict[m],
            linewidth=1.5,
            zorder=zorderDict[m],
        )
    ax.set_ylabel("Relative Hit Rate", fontsize=16)
    ax.set_xlabel("LRU Application Client Portion", fontsize=16)
    ax.set_ylim(0.6, 1.8)
    ax.tick_params(labelsize=14)
    ax.grid(linewidth=0.3)
    ax.legend(
        fontsize=14,
        frameon=False,
        labelspacing=0.2,
        ncol=2,
        columnspacing=1.2,
        handletextpad=0.2,
        bbox_to_anchor=(1, 1.06),
    )
    if not os.path.exists("figs"):
        os.mkdir("figs")
    figName = "figs/fig20.pdf"
    plt.savefig(figName, format="pdf", bbox_inches="tight")


def plot_fig21(res_dict: dict):
    method_list = [
        "sample-lru",
        "sample-lfu",
        "sample-adaptive",
        "cliquemap-precise-lru",
        "cliquemap-precise-lfu",
    ]
    _, ax = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    base = res_dict["sample-lru"]["hit_rate"]
    for i, m in enumerate(method_list):
        y = np.array(res_dict[m]["hit_rate"]) / np.array(base)
        x = [i for i in range(len(y))]
        ax.plot(
            x,
            y,
            linestyle=lineStyleDict[m],
            color=lineColorDict[m],
            marker=lineMarkerDict[m],
            markerfacecolor="none",
            label=methodLabelDict[m],
            linewidth=1.5,
            zorder=zorderDict[m],
        )
    ax.set_ylabel("Relative Hit Rate", fontsize=16)
    ax.set_xlabel("Client Number", fontsize=16)
    ax.set_ylim(0.4, 1.6)
    ax.set_xticks([i for i in range(10)])
    ax.set_xticklabels(["16", "32", "48", "64", "80", "96", "112", "128", "144", "160"])
    ax.tick_params(labelsize=14)
    ax.grid(linewidth=0.3)
    ax.legend(
        fontsize=14,
        loc="upper left",
        frameon=False,
        labelspacing=0.2,
        ncol=2,
        columnspacing=1.2,
        handletextpad=0.3,
        bbox_to_anchor=(0, 1.06),
    )
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig21.pdf", format="pdf", bbox_inches="tight")


def plot_fig22(adaptive_res: dict, lru_res: dict, lfu_res: dict):
    data = {
        "sample-lru": lru_res,
        "sample-lfu": lfu_res,
        "sample-adaptive": adaptive_res,
    }
    method_list = ["sample-lru", "sample-lfu", "sample-adaptive"]

    fig, ax = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    for m in method_list:
        color = lineColorDict[m]
        if m == "sample-lru":
            color = lineColorDict["cliquemap-precise-lru"]
        elif m == "sample-lfu":
            color = lineColorDict["cliquemap-precise-lfu"]
        ax.plot(
            data[m]["hr_coarse"][1:-1],
            color=color,
            linestyle=lineStyleDict[m],
            label=methodLabelDict[m],
            linewidth=1,
        )

    ax.set_ylim(0.5, 0.9)
    ax.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9])
    ax.set_ylabel("Hit Rate", fontsize=16)
    ax.set_xlabel("Time (seconds)", fontsize=16)
    ax.set_xticks([0, 100, 200, 300, 400])
    ax.tick_params(labelsize=14)
    ax.grid(axis="y", linewidth=0.5)
    ax.set_xticklabels(["0", "50", "100", "150", "200"])
    ax.tick_params(labelsize=14)
    ax.legend(
        fontsize=14,
        bbox_to_anchor=(1.15, 1.23),
        frameon=False,
        labelspacing=0.2,
        ncol=3,
        columnspacing=0.5,
        handletextpad=0.3,
    )

    # set y labels
    ax.axvline(80, color="gray", linestyle="--", linewidth=0.5)
    ax.axvline(160, color="gray", linestyle="--", linewidth=0.5)
    ax.axvline(240, color="gray", linestyle="--", linewidth=0.5)
    ax.axvline(320, color="gray", linestyle="--", linewidth=0.5)

    # add texts
    ax.text(3, 0.8, "10%", fontsize=16)
    ax.text(0, 0.76, "trace", fontsize=16)
    ax.text(93, 0.58, "20%", fontsize=16)
    ax.text(90, 0.54, "trace", fontsize=16)
    ax.text(173, 0.58, "30%", fontsize=16)
    ax.text(170, 0.54, "trace", fontsize=16)
    ax.text(253, 0.58, "40%", fontsize=16)
    ax.text(250, 0.54, "trace", fontsize=16)
    ax.text(333, 0.58, "50%", fontsize=16)
    ax.text(330, 0.54, "trace", fontsize=16)
    plt.savefig("figs/fig22.pdf", bbox_inches="tight")


def plot_fig23(res: dict):
    method_list = [
        "lru",
        "lfu",
        "mru",
        "gds",
        "lirs",
        "fifo",
        "size",
        "gdsf",
        "lrfu",
        "lruk",
        "lfuda",
        "hyperbolic",
    ]

    _, ax_L = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    ax_R = ax_L.twinx()
    xList = np.arange(len(method_list))
    totalWidth = 0.5
    width = totalWidth
    yList = [res[f"sample-{m}"]["tpt"] / 1000000 for m in method_list]
    ax_L.bar(
        xList,
        yList,
        width=width,
        edgecolor="black",
        fill=True,
        label="Throughput",
        color=barColorDict["sample-adaptive"],
        linewidth=0.2,
        hatch=barHatchDict["sample-adaptive"],
        zorder=100,
    )
    yList = [res[f"sample-{m}"]["hr"] for m in method_list]
    ax_R.plot(
        xList,
        yList,
        linestyle=lineStyleList[0],
        color=lineColorDict["cliquemap-precise-lru"],
        marker=lineMarkerDict["cliquemap-precise-lru"],
        markerfacecolor="none",
        label="Hit Rate",
        linewidth=2,
        zorder=100,
    )
    ax_L.set_ylabel("Throughput (Mops/s)", fontsize=15)
    ax_L.set_ylim(1, 3.5)
    ax_L.set_xticks([i for i in range(len(method_list))])
    ax_L.tick_params(labelsize=14, axis="y")
    ax_R.tick_params(labelsize=14, axis="y")
    ax_L.set_xticklabels([i.upper() for i in method_list], fontsize=14, rotation=35)
    ax_L.legend(
        fontsize=14, frameon=False, bbox_to_anchor=(0.52, 1.21), handletextpad=0.3
    )
    ax_L.grid(zorder=-1, linewidth=0.5)
    ax_R.set_ylabel("Hit Rate", fontsize=15)
    ax_R.set_ylim(0.3, 0.8)
    ax_R.legend(
        fontsize=14, frameon=False, bbox_to_anchor=(1.05, 1.21), handletextpad=0.3
    )
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig23.pdf", format="pdf", bbox_inches="tight")


def plot_fig24(res: dict):
    method_list = [
        "sample-adaptive",
        "sample-adaptive-async-nfc",
        "sample-adaptive-sync-nfc",
        "sample-adaptive-heavy",
        "sample-adaptive-naive",
    ]

    _, ax = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    xList = np.arange(len(method_list))
    totalWidth = 0.4
    width = totalWidth
    yList = np.array([res[m]["tpt"] for m in method_list]) / 1000000
    ax.bar(
        xList,
        yList,
        width=width,
        edgecolor="black",
        fill=True,
        label="Throughput",
        color=barColorDict["sample-adaptive"],
        linewidth=0.2,
        hatch=barHatchDict["sample-adaptive"],
        zorder=100,
    )
    # ax.set_xlabel('Method', fontsize=16)
    ax.set_xticks([i for i in range(5)])
    ax.set_xticklabels(["Ditto", "-FC", "-LWU", "-LWH", "-SFHT"], fontsize=17)
    ax.set_ylabel("Throughput (Mops/s)", fontsize=16)
    ax.set_xlabel("    ", fontsize=16)
    ax.set_ylim(1, 2.8)
    ax.set_yticks([1, 1.5, 2, 2.5])
    ax.tick_params(labelsize=14, axis="y")
    ax.grid(zorder=0, linewidth=0.3)
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig24.pdf", format="pdf", bbox_inches="tight")


def plot_fig24_more(res: dict, workload):
    method_list = [
        "sample-adaptive",
        "sample-adaptive-async-nfc",
        "sample-adaptive-sync-nfc",
        "sample-adaptive-heavy",
        "sample-adaptive-naive",
    ]

    _, ax = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    xList = np.arange(len(method_list))
    totalWidth = 0.4
    width = totalWidth
    yList = np.array([res[m]["tpt"] for m in method_list]) / 1000000
    ax.bar(
        xList,
        yList,
        width=width,
        edgecolor="black",
        fill=True,
        label="Throughput",
        color=barColorDict["sample-adaptive"],
        linewidth=0.2,
        hatch=barHatchDict["sample-adaptive"],
        zorder=100,
    )
    # ax.set_xlabel('Method', fontsize=16)
    ax.set_xticks([i for i in range(5)])
    ax.set_xticklabels(["Ditto", "-FC", "-LWU", "-LWH", "-SFHT"], fontsize=17)
    ax.set_ylabel("Throughput (Mops/s)", fontsize=16)
    ax.set_xlabel("    ", fontsize=16)
    ax.set_ylim(1, 2.8)
    ax.set_yticks([1, 1.5, 2, 2.5])
    ax.tick_params(labelsize=14, axis="y")
    ax.grid(zorder=0, linewidth=0.3)
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig(f"figs/fig24_{workload}.pdf", format="pdf", bbox_inches="tight")


def plot_fig25(_res: dict):
    fc_data = {}
    cache_size_list = [
        0,
        1024,
        10240,
        102400,
        1024 * 1024,
        5 * 1024 * 1024,
        10 * 1024 * 1024,
        50 * 1024 * 1024,
        100 * 1024 * 1024,
    ]
    tpt_list = []
    p50_list = []
    p99_list = []
    for fc_size in cache_size_list:
        tpt_list.append(_res[f"{fc_size}"]["tpt"])
        p50_list.append(_res[f"{fc_size}"]["p50"])
        p99_list.append(_res[f"{fc_size}"]["p99"])
    fc_data["tpt"] = tpt_list
    fc_data["p50"] = p50_list
    fc_data["p99"] = p99_list

    _, ax_L = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    ax_R = ax_L.twinx()
    xList = np.arange(9)
    totalWidth = 0.5
    width = totalWidth
    yList = np.array(fc_data["tpt"]) / 1000000
    ax_L.bar(
        xList,
        yList,
        width=width,
        edgecolor="black",
        fill=True,
        label="Throughput",
        color=barColorDict["sample-adaptive"],
        linewidth=0.2,
        hatch=barHatchDict["sample-adaptive"],
        zorder=100,
    )
    ax_R.plot(
        xList,
        fc_data["p99"],
        linestyle=lineStyleList[0],
        color=lineColorDict["cliquemap-precise-lru"],
        marker=lineMarkerDict["cliquemap-precise-lru"],
        markerfacecolor="none",
        label="p99",
        linewidth=2,
    )
    ax_R.plot(
        xList,
        fc_data["p50"],
        linestyle=lineStyleList[1],
        color=lineColorDict["cliquemap-precise-lfu"],
        marker=lineMarkerDict["cliquemap-precise-lfu"],
        markerfacecolor="none",
        label="p50",
        linewidth=2,
    )
    ax_L.set_xlabel("Freqency-Counter Cache Size", fontsize=17)
    ax_L.set_ylabel("Throughput (Mops/s)", fontsize=15)
    ax_L.set_ylim(8, 17)
    ax_L.set_yticks([8 + i for i in range(0, 10, 2)])
    ax_L.set_xticks([i for i in range(9)])
    ax_L.set_xticklabels(
        ["0", "1K", "10K", "100K", "1M", "5M", "10M", "50M", "100M"], fontsize=12
    )
    ax_L.tick_params(labelsize=12, axis="y")
    ax_R.tick_params(labelsize=12, axis="y")
    ax_L.legend(
        fontsize=16, frameon=False, handletextpad=0.3, bbox_to_anchor=(0.62, 1.06)
    )
    ax_L.grid(zorder=0)
    ax_R.set_ylabel("Latency (us)", fontsize=14)
    ax_R.legend(
        fontsize=16,
        frameon=False,
        handletextpad=0.3,
        labelspacing=0.2,
        bbox_to_anchor=(1, 1.06),
    )
    ax_R.set_ylim(10, 50)
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig("figs/fig25.pdf", format="pdf", bbox_inches="tight")


def plot_fig25_more(_res: dict, workload):
    fc_data = {}
    cache_size_list = [
        0,
        1024,
        10240,
        102400,
        1024 * 1024,
        5 * 1024 * 1024,
        10 * 1024 * 1024,
        50 * 1024 * 1024,
        100 * 1024 * 1024,
    ]
    tpt_list = []
    p50_list = []
    p99_list = []
    for fc_size in cache_size_list:
        tpt_list.append(_res[f"{fc_size}"]["tpt"])
        p50_list.append(_res[f"{fc_size}"]["p50"])
        p99_list.append(_res[f"{fc_size}"]["p99"])
    fc_data["tpt"] = tpt_list
    fc_data["p50"] = p50_list
    fc_data["p99"] = p99_list

    _, ax_L = plt.subplots(1, 1, figsize=(4, 2.5), dpi=300)
    ax_R = ax_L.twinx()
    xList = np.arange(9)
    totalWidth = 0.5
    width = totalWidth
    yList = np.array(fc_data["tpt"]) / 1000000
    ax_L.bar(
        xList,
        yList,
        width=width,
        edgecolor="black",
        fill=True,
        label="Throughput",
        color=barColorDict["sample-adaptive"],
        linewidth=0.2,
        hatch=barHatchDict["sample-adaptive"],
        zorder=100,
    )
    ax_R.plot(
        xList,
        fc_data["p99"],
        linestyle=lineStyleList[0],
        color=lineColorDict["cliquemap-precise-lru"],
        marker=lineMarkerDict["cliquemap-precise-lru"],
        markerfacecolor="none",
        label="p99",
        linewidth=2,
    )
    ax_R.plot(
        xList,
        fc_data["p50"],
        linestyle=lineStyleList[1],
        color=lineColorDict["cliquemap-precise-lfu"],
        marker=lineMarkerDict["cliquemap-precise-lfu"],
        markerfacecolor="none",
        label="p50",
        linewidth=2,
    )
    ax_L.set_xlabel("Freqency-Counter Cache Size", fontsize=17)
    ax_L.set_ylabel("Throughput (Mops/s)", fontsize=15)
    ax_L.set_ylim(8, 17)
    ax_L.set_yticks([8 + i for i in range(0, 10, 2)])
    ax_L.set_xticks([i for i in range(9)])
    ax_L.set_xticklabels(
        ["0", "1K", "10K", "100K", "1M", "5M", "10M", "50M", "100M"], fontsize=12
    )
    ax_L.tick_params(labelsize=12, axis="y")
    ax_R.tick_params(labelsize=12, axis="y")
    ax_L.legend(
        fontsize=16, frameon=False, handletextpad=0.3, bbox_to_anchor=(0.62, 1.06)
    )
    ax_L.grid(zorder=0)
    ax_R.set_ylabel("Latency (us)", fontsize=14)
    ax_R.legend(
        fontsize=16,
        frameon=False,
        handletextpad=0.3,
        labelspacing=0.2,
        bbox_to_anchor=(1, 1.06),
    )
    ax_R.set_ylim(10, 50)
    if not os.path.exists("figs"):
        os.mkdir("figs")
    plt.savefig(f"figs/fig25_{workload}.pdf", format="pdf", bbox_inches="tight")
