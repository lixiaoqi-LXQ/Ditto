import time
import json
from sys import argv
import numpy as np

from utils.utils import save_time, save_res, dump_output
from utils.cmd_manager import CMDManager
from utils.settings import get_make_cmd
from cluster_setting import *


# config infomation
work_dir = f"{EXP_HOME}/experiments/ycsb_test"
workload = "ycsbc"
client_num = 32
num_CN = client_num // NUM_CLIENT_PER_NODE + (client_num % NUM_CLIENT_PER_NODE != 0)
workload_size = 10**7
run_time = 20


def run_1_pass(cmd_manager: CMDManager, cache_size: int, build=True):
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


if __name__ == "__main__":
    st = time.time()

    res = {}
    cmd_manager = CMDManager(cluster_ips)
    if len(argv) > 1:
        times = int(argv[1])
        cache_size = 10 * workload_size * 0.01
        # cache_size = 0
        hitrates, ncaches, p50s, p90s, p99s, p999s, tpts = [[] for _ in range(7)]
        for i in range(times):
            json_res = run_1_pass(cmd_manager, cache_size=cache_size, build=(i == 0))
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
    else:
        size_step = int(0.5 * workload_size * 0.01)
        start = size_step
        end = int(10 * workload_size * 0.01 + size_step)
        print("ready to run {} iters", len(range(start, end, size_step)))
        for cache_size in range(start, end, size_step):
            json_res = run_1_pass(cmd_manager, cache_size)
            res[cache_size] = json_res
    print(res)
    save_res("client_cache", res)

    et = time.time()
    save_time(argv[0], et - st)
