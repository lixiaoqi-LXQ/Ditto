from utils.plots import (
    plot_cache_size_matrices,
    plot_compare_LRU_and_DUMB,
    plot_compare_three,
)
import json


def f1():
    res = {}
    with open("./results/c1_evictDUMBR_w80r20_10w30w.json", "r") as f:
        res_cache = dict(json.load(f))
    with open("./results/c1_RDMA_w0r20_10w30w.json", "r") as f:
        res_RDMA = dict(json.load(f))
    plot_cache_size_matrices(res_cache, res_RDMA, "c1_DUMBT_w80r20_10w30w")


def f2():
    DUMBS_RES_FILE = "results/fully-opt/ycsbc_c1_evict_DUMB_SIMPLE_w80r20_10w30w.json"
    DUMBR_RES_FILE = "results/fully-opt/ycsbc_c1_evict_DUMB_RANDOM_w80r20_10w30w.json"
    LRU_RES_FILE = "results/fully-opt/ycsbc_c1_evict_LRU_w80r20_10w30w.json"
    RDMA_RES_FILE = "results/fully-opt/ycsbc_c1_evict_RDMA_w80r20_10w30w.json"
    with open(DUMBS_RES_FILE, "r") as f:
        res_DUMB_SIMPLE = dict(json.load(f))
    with open(DUMBR_RES_FILE, "r") as f:
        res_DUMB_RANDOM = dict(json.load(f))
        # res_DUMB_RANDOM = {key: res_DUMB_RANDOM[key] for key in res_DUMB_SIMPLE}
    with open(LRU_RES_FILE, "r") as f:
        res_LRU = dict(json.load(f))
        # res_LRU_sample = {key: res_LRU[key] for key in res_DUMB_SIMPLE}
    with open(RDMA_RES_FILE, "r") as f:
        res_RDMA = dict(json.load(f))
    # plot_compare_LRU_and_DUMB(res_LRU, res_DUMB, res_RDMA)
    plot_compare_three(res_LRU, res_DUMB_RANDOM, res_DUMB_SIMPLE, res_RDMA)


if __name__ == "__main__":
    f2()
