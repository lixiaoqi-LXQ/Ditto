from utils.plots import plot_cache_size_matrices
import json

if __name__ == "__main__":
    res = {}
    with open("./results/client_cache_warmup2full.json", "r") as f:
        res['cache'] = dict(json.load(f))
    with open("./results/client_cache_RDMA.json", "r") as f:
        res['RDMA'] = dict(json.load(f))
    plot_cache_size_matrices(res)
    

