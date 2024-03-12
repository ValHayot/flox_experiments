import parsl
import argparse
import time

from parsl.config import Config
from parsl.launchers import SrunLauncher
from parsl.providers import SlurmProvider
from parsl.executors import HighThroughputExecutor
from parsl import python_app

from proxystore.store import register_store
from proxystore.store import Store
from proxystore.connectors.file import FileConnector
from proxystore.connectors.redis import RedisConnector
from proxystore_ex.connectors.dim.margo import MargoConnector

@python_app
def platform():
    import platform
    return platform.uname()


def priming():
    future = platform()
    print("Launched task.. waiting")
    print(f"Result : {future.result()}")

    
@python_app
def sleeper(config, sleep_dur=0, input_data="", output_data_volume:int=1):
    import time
    import random
    from proxystore.store import Store
    from proxystore.store import register_store

    time.sleep(sleep_dur)

    #if 'Margo' in config['connector_type']:
    #    config['connector_config']['port'] = random.randint(5001, 6000)

    output_string =  b'0' * output_data_volume * 10**6

    if config is not None:
        store = Store.from_config(config)
        register_store(store, exist_ok=True)
        output_string = store.proxy(output_string)

    return output_string


def test_sequence(num_workers, task_count=1, sleep_dur=0, input_data=0, output_data=0, store='parsl'):
    prefix = f"[{num_workers=}][{task_count=}][{sleep_dur=}][{input_data=}][{output_data=}]"

    start = time.time()
    config=None


    input_string = b'0' * input_data * 10**6

    if store != 'parsl':
        if store == 'redis':
            connector = RedisConnector(hostname='10.22.11.20', port=6379)
        elif store == 'file':
            connector = FileConnector(store_dir='/home/vhayot/flox_experiments/data')
        else:
            connector = MargoConnector(port=7000, protocol='ofi+verbs')
        store = Store('flox-store', connector)  
        config = store.config()
        input_string = store.proxy(input_string)

    futures = [sleeper(config, sleep_dur, input_string, output_data) for i in range(task_count)]
    launch_done = time.time() - start
    [future.result() for future in futures]
    exec_done = time.time() - start

    print(prefix + f"Launched tasks in {launch_done:.3f}s")
    print(prefix + f"Finished noop tasks in {exec_done:.3f}s")
    throughput = task_count / exec_done
    print(prefix + f"Throughput  {throughput:.3f} Tasks/s")
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nodes", default="1",
                        help="Count of apps to launch")
    parser.add_argument("-w", "--workers_per_node", default="1",
                        help="Count of apps to launch")
    parser.add_argument("-c", "--count", default='',
                        help="Number of tasks to launch")
    parser.add_argument("-s", "--store", default='parsl', choices=['parsl', 'redis', 'file', 'margo'])

    args = parser.parse_args()

    config = Config(
    executors=[
        HighThroughputExecutor(
            label="Expanse",
            # worker_logdir_root='YOUR_LOGDIR_ON_COMET',
            max_workers=int(args.workers_per_node),
            prefetch_capacity=100,
            provider=SlurmProvider(
                'compute',
                # 'debug',
                # account="anl113",
                account="chi150",
                launcher=SrunLauncher(),
                # string to prepend to #SBATCH blocks in the submit
                # script to the scheduler
                scheduler_options='',
                # Command to be run before starting a worker, such as:
                # 'module load Anaconda; source activate parsl_env'.
                worker_init='source ~/spack/share/spack/setup-env.sh; spack env activate mochi -p',
                walltime='00:30:00',
                init_blocks=1,
                max_blocks=1,
                nodes_per_block=int(args.nodes),
            ),
        )
    ]
    )

    parsl.load(config)
    priming()

    if not args.count:
        count_range = [100, 200]
    else:
        count_range = [int(args.count)]
        
    for data_volume in [8, 16, 32]:
        for task_count in count_range:
            for sleep_dur in [0, 1]:
                test_sequence(num_workers=int(args.nodes) * int(args.workers_per_node),
                              task_count=task_count,
                              sleep_dur=sleep_dur,
                              input_data=data_volume,
                              output_data=data_volume,
                              store=args.store)
