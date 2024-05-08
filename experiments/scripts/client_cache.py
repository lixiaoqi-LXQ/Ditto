import time
import json
import numpy as np

from sys import argv
from itertools import product
from utils.utils import save_time, save_res, dump_output
from utils.cmd_manager import CMDManager
from utils.settings import (
    get_cache_config_cmd,
    get_make_cmd,
    get_freq_cache_cmd,
    get_mn_cpu_cmd,
)
from cluster_setting import *
from utils.plots import plot_fig15_16


# config infomation
workload = "ycsbc"
client_num = 1
num_CN = client_num // NUM_CLIENT_PER_NODE + (client_num % NUM_CLIENT_PER_NODE != 0)
workload_size = 10**7
run_time = 20


def ycsb_run_1_pass(cache_size: int, build=True):
    work_dir = f"{EXP_HOME}/experiments/ycsb_test"
    cmd_manager = CMDManager(cluster_ips)
    cache_size = int(cache_size)
    # reset cluster
    cmd_manager.execute_on_nodes([master_id], RESET_MASTER_CMD)
    cmd_manager.execute_on_nodes(
        [i for i in range(len(cluster_ips)) if i != master_id], RESET_WORKER_CMD
    )

    # rebuild project
    if build:
        MAKE_CMD = get_make_cmd(
            build_dir,
            "sample-adaptive",
            "ycsb",
            None,
            {"client_cache_limit": cache_size},
        )
        print(
            "build with cache size {}({}% workload)".format(
                cache_size, cache_size / workload_size * 100
            )
        )
        cmd_manager.execute_once(MAKE_CMD, hide=True)
    # set cache size configuration
    CACHE_CONFIG_CMD = get_cache_config_cmd(config_dir, "ycsb", None)
    cmd_manager.execute_once(CACHE_CONFIG_CMD)
    # set freq_cache configuration
    FC_CONFIG_CMD = get_freq_cache_cmd(config_dir, default_fc_size)
    cmd_manager.execute_once(FC_CONFIG_CMD)
    # set MN CPU
    MN_CPU_CMD = get_mn_cpu_cmd(config_dir, 1)
    cmd_manager.execute_once(MN_CPU_CMD)

    # start controller and MN
    print("start running...")
    controller_prom = cmd_manager.execute_on_node(
        master_id,
        f"cd {work_dir} && ./run_controller.sh sample-adaptive 1 {client_num} {workload} {run_time}",
    )
    mn_prom = cmd_manager.execute_on_node(
        mn_id, f"cd {work_dir} && ./run_server.sh sample-adaptive"
    )

    # start CNs
    time.sleep(5)
    c_prom_list = []
    for i in range(num_CN):
        st_cid = i * NUM_CLIENT_PER_NODE + 1
        if i == num_CN - 1 and client_num % NUM_CLIENT_PER_NODE != 0:
            c_prom = cmd_manager.execute_on_node(
                client_ids[i],
                f"cd {work_dir} && ./run_client_master.sh sample-adaptive {st_cid} {workload} {client_num % NUM_CLIENT_PER_NODE} {client_num} {run_time}",
            )
        else:
            c_prom = cmd_manager.execute_on_node(
                client_ids[i],
                f"cd {work_dir} && ./run_client_master.sh sample-adaptive {st_cid} {workload} {NUM_CLIENT_PER_NODE} {client_num} {run_time}",
            )
        c_prom_list.append(c_prom)

    # wait clients
    for i, c_prom in enumerate(c_prom_list):
        res = c_prom.join()
        dump_output(
            "stdout-client-client-cache",
            f"===============client-{i+1}-stdout===============\n" + res.stdout,
            i != 0,
        )
    # wait MN
    res = mn_prom.join()
    dump_output("stdout-server-client-cache", res.stdout)

    raw_res = controller_prom.join()
    line = raw_res.tail("stdout", 1).strip()
    json_res = json.loads(line)
    return json_res


def real_workload_run(local_cache_size):
    work_dir = f"{EXP_HOME}/experiments/workload_throughput"
    client_num = 64
    local_cache_size = int(local_cache_size)

    cmd_manager = CMDManager(cluster_ips)
    # reset cluster
    cmd_manager.execute_on_nodes([master_id], RESET_MASTER_CMD)
    cmd_manager.execute_on_nodes(
        [i for i in range(len(cluster_ips)) if i != master_id], RESET_WORKER_CMD
    )

    # set freq_cache configuration
    FC_CONFIG_CMD = get_freq_cache_cmd(config_dir, default_fc_size)
    cmd_manager.execute_once(FC_CONFIG_CMD)
    # set MN CPU
    MN_CPU_CMD = get_mn_cpu_cmd(config_dir, 1)
    cmd_manager.execute_once(MN_CPU_CMD)

    method_list = [
        "sample-adaptive",
        # "sample-lru",
        # "sample-lfu",
        # "cliquemap-precise-lru",
        # "cliquemap-precise-lfu",
    ]
    workload_list = [
        "twitter020-10m",
        # "twitter049-10m",
        # "twitter042-10m",
        # "webmail-all",
        # "ibm044-10m",
    ]
    cache_size_list = ["0.2", "0.1", "0.05", "0.01"]

    all_res = {}
    for wl, cache_size in product(workload_list, cache_size_list):
        # All methods in this experiment use the same compile options
        MAKE_CMD = get_make_cmd(
            build_dir,
            "sample-adaptive",
            wl,
            cache_size,
            {"client_cache_limit": local_cache_size},
        )
        print("building...")
        cmd_manager.execute_once(MAKE_CMD, hide=True)
        CACHE_CONFIG_CMD = get_cache_config_cmd(config_dir, wl, cache_size)
        cmd_manager.execute_once(CACHE_CONFIG_CMD)
        for method in method_list:
            print(
                f"Start executing {method} with {client_num} clients under {wl} with cache size {cache_size}, planning to run 20s"
            )
            # start Controller and MN
            controller_prom = cmd_manager.execute_on_node(
                master_id,
                f"cd {work_dir} && ./run_controller.sh {method} 1 {client_num} {wl}",
            )
            mn_prom = cmd_manager.execute_on_node(
                mn_id, f"cd {work_dir} && ./run_server.sh {method}"
            )

            # start Clients
            time.sleep(5)
            c_prom_list = []
            for i in range(1):
                st_cid = i * NUM_CLIENT_PER_NODE + 1
                c_prom = cmd_manager.execute_on_node(
                    client_ids[i],
                    f"cd {work_dir} && ./run_client_master.sh {method} {st_cid} {wl} {NUM_CLIENT_PER_NODE} {client_num}",
                )
                c_prom_list.append(c_prom)
            assert len(c_prom_list) * NUM_CLIENT_PER_NODE >= client_num

            # wait for Clients and MN
            for c_prom in c_prom_list:
                c_prom.join()
            mn_prom.join()

            raw_res = controller_prom.join()
            line = raw_res.tail("stdout", 1).strip()
            res = json.loads(line)
            if wl not in all_res:
                all_res[wl] = {}
            if method not in all_res[wl]:
                all_res[wl][method] = {}
            if cache_size not in all_res[wl][method]:
                all_res[wl][method][cache_size] = {}
            all_res[wl][method][cache_size] = res

    # save res
    save_res("fig15_16", all_res)

    plot_fig15_16(all_res)

    et = time.time()
    save_time("fig15_16", et - st)


if __name__ == "__main__":
    st = time.time()
    # real_workload_run(workload_size * 0.01 * 5)
    # exit()

    res = {}
    if len(argv) > 1:
        times = int(argv[1])
        cache_size = 20 * workload_size * 0.01
        hitrates, ncaches, p50s, p90s, p99s, p999s, tpts = [[] for _ in range(7)]
        for i in range(times):
            json_res = ycsb_run_1_pass(cache_size=cache_size, build=(i == 0))
            print(json_res)
            hitrates.append(json_res["hit-rate-local"])
            ncaches.append(json_res["local-cache-num(before trans)"])
            tpts.append(json_res["tpt"])
            p50s.append(json_res["p50"])
            p90s.append(json_res["p90"])
            p99s.append(json_res["p99"])
            p999s.append(json_res["p999"])
        res = {
            "hit-rate": np.average(hitrates),
            "local-cache-num(before trans)": np.average(ncaches),
            "tpt": np.average(tpts),
            "p50": np.average(p50s),
            "p90": np.average(p90s),
            "p99": np.average(p99s),
            "p999": np.average(p999s),
        }
        res = json.loads(json.dumps(res))
        if times == 1:
            res = json_res
    else:
        size_step = int(1 * workload_size * 0.01)
        start = size_step
        end = int(100 * workload_size * 0.01 + size_step)
        print("ready to run {} iters", len(range(start, end, size_step)))
        for cache_size in range(start, end, size_step):
            json_res = ycsb_run_1_pass(cache_size)
            res[cache_size] = json_res
    print(res)
    save_res("client_cache", res)

    et = time.time()
    save_time(argv[0], et - st)
