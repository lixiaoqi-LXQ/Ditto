from utils.plots import plot_cache_size_matrices, plot_compare_LRU_and_DUMB
import json


def f1():
    res = {}
    with open("./results/client_cache_evictDumb.json", "r") as f:
        res["cache"] = dict(json.load(f))
    with open("./results/client_cache_RDMA.json", "r") as f:
        res["RDMA"] = dict(json.load(f))
    plot_cache_size_matrices(res, "evictDumb")


def f2():
    with open("./results/client_cache_evictDUMB.json", "r") as f:
        res_DUMB = dict(json.load(f))
    with open("./results/client_cache_evictLRU.json", "r") as f:
        res_LRU = dict(json.load(f))
    with open("./results/client_cache_RDMA.json", "r") as f:
        res_RDMA = dict(json.load(f))
    plot_compare_LRU_and_DUMB(res_LRU, res_DUMB, res_RDMA)


if __name__ == "__main__":
    f2()
