# -*- coding: utf-8 -*-

import argparse
import time
from multiprocessing import (
    Process,
    Queue,
    cpu_count,
    Manager,
)

import tqdm
import ujson
from prettytable import PrettyTable

from constants import *
from environment import Environment
from errors import *
from logger import LOGGER
from utils import (
    divide,
)

parser = argparse.ArgumentParser(description='DBChecker cli')
parser.add_argument('-f', '--file', type=str)
parser.add_argument('-s', '--bound_size', type=int, default=999999999)
parser.add_argument('-t', '--timeout', type=int, default=TIMEOUT)
parser.add_argument('-m', '--mode', type=str, default='train', choices=['train', 'eval'])
# multiprocessing might decrease the CPU's performance on each core, but it decreases the total time cost
parser.add_argument('-c', '--cores', type=int, default=1, choices=list(range(1, 1 + cpu_count())))
parser.add_argument('-i', '--integrity_constraint', default=1, choices=[0, 1], type=int)
parser.add_argument('-o', '--out_file', type=str, default=None)
args = parser.parse_args()


def verify(schema, constraint, query1, query2, bound_size, queue: Queue):
    err_info = None
    with Environment(timer=True, generate_code=True) as env:
        for name, db in schema.items():
            env.create_database(db, bound_size=bound_size, name=name)
        if args.integrity_constraint and constraint is not None:
            env.add_constraints(constraint)
        env.save_checkpoints()
        env.reload_checkpoints()
        try:
            result = env.analyze(query1, query2)
            if result == False:
                raise NotEquivalenceError()
            else:
                state = STATE.EQUIV
        except SyntaxError as err:
            err_info = str(err)
            state = STATE.SYN_ERR
        except NotEquivalenceError as err:
            err_info = str(err)
            state = STATE.NON_EQUIV
        except TimeoutError as err:
            err_info = str(err)
            state = STATE.TIMEOUT
        except NotSupportedError as err:
            err_info = str(err)
            state = STATE.NOT_SUP_ERR
        except UnknownError as err:
            err_info = str(err)
            state = STATE.UNKNOWN
        except NotImplementedError as err:
            err_info = str(err)
            state = STATE.NOT_IMPL_ERR
        except Exception as err:
            err_info = str(err)
            state = STATE.OTHER_ERR
        counterexample = env.sql_code if isinstance(env.sql_code, str) else None
        if env.solving_time is None:
            outs = [state, round(time.time() - env.traversing_time, 6), None, counterexample, err_info]
        else:
            outs = [state, env.traversing_time, env.solving_time, counterexample, err_info]
        for o in outs:
            queue.put(o)


def process_ends_with_max_timeout(
        index, schema, constraint, query1, query2, max_bound_size, states, time_cost,
        timeout, queue: Queue
):
    result = {
        'index': index,
        'pair': [query1, query2],
        'states': [],
        'times': [],
        'counterexample': None,
        'err': None,
    }
    if states is not None and time_cost is not None:
        result['states'] = states
        result['times'] = time_cost

    pbar = tqdm.tqdm(total=max_bound_size, desc=f'Bound size: {0:5d} | Thread: {1:3d}', )

    bound_size = len(result['states']) + 1
    pbar.set_description(f'Bound size: {bound_size:5d} | Thread: {1:3d}', refresh=False)
    pbar.update(bound_size)
    queue.empty()
    proc = Process(
        target=verify,
        args=(schema, constraint, query1, query2, bound_size, queue,),
    )
    proc.start()

    start = time.time()
    while time.time() - start <= timeout:
        if not proc.is_alive():
            # All the processes are done, break now.
            try:
                state, traversing_time, solving_time, counterexample, err = [queue.get() for _ in range(queue.qsize())]
                result['states'].append(state)
                result['times'].append([traversing_time, solving_time])
                result['counterexample'] = counterexample
                result['err'] = err
            except ValueError:
                # out of memory
                state = STATE.OOM
                result['states'].append(state)
                result['times'].append(None)

            if state == STATE.EQUIV:
                # only continute if queries are = or !=
                bound_size = len(result['states']) + 1
                pbar.set_description(f'Bound size: {bound_size:5d} | Thread: {1:3d}', refresh=False)
                pbar.update(bound_size)
                queue.empty()
                proc = Process(
                    target=verify,
                    args=(schema, constraint, query1, query2, bound_size, queue,),
                )
                proc.start()
            else:
                # not support
                break
        else:
            time.sleep(0.1)  # Just to avoid hogging the CPU
    else:
        # We only enter this if we didn't 'break' above.
        LOGGER.debug("timed out, killing all processes")
        proc.terminate()
        proc.join()
        result['states'].append(STATE.TIMEOUT)
        result['times'].append(None)
    return result


def core(pbar, out_file, desc, timeout, worker_idx):
    pbar = tqdm.tqdm(pbar, desc=desc, mininterval=10)

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w') as writer:
        for parameters in pbar:
            file_path = parameters.pop(-1)
            manager = Manager()
            queue = manager.Queue()
            out = process_ends_with_max_timeout(*parameters, timeout, queue)
            # to log for check
            out['file'] = file_path
            out['schema'] = parameters[1]
            out['constraint'] = parameters[2]
            print(ujson.dumps(out, ensure_ascii=False), file=writer)


def train(args):
    with open(args.file, 'r') as reader:
        parameters = []
        for file in reader:
            context = ujson.loads(file)
            index = context['index']
            schema = context['schema']
            pair = context['pair']
            if context.get('contain_unsupported_constraints', False):
                constraint = None
            else:
                constraint = context.get('constraint', None)
            if 'file' in context:
                file_path = context['file']
            elif 'name' in context:
                file_path = context['name']
            elif 'benchmark' in context:
                file_path = context['benchmark']
            states = timecost = None
            parameters.append([index, schema, constraint, *pair, args.bound_size, states, timecost, file_path])
        # out_file = args.file[:args.file.rfind('.jsonlines')] + '.out'
        # if os.path.exists(out_file):
        #     with open(out_file, 'r') as reader:
        #         for idx, line in enumerate(reader):
        #             line = ujson.loads(line)
        #             parameters[idx][-2] = line['states']
        #             parameters[idx][-1] = line['times']
        count = len(parameters)

        if args.cores == 1:
            core(
                parameters,
                args.out_file,
                f'Bound size: {args.bound_size:3d} | Thread: {1:3d}',
                args.timeout,
                worker_idx=1,
            )
        else:
            parameters = list(divide(parameters, partitions=args.cores))
            procs = []
            for worker_idx in range(len(parameters)):
                proc = Process(
                    target=core,
                    args=(
                        parameters[worker_idx],
                        args.out_file + str(worker_idx),
                        f'Bound size: {args.bound_size:3d} | Thread: {worker_idx:3d}',
                        args.timeout,
                        worker_idx,
                    ),
                )
                proc.start()
                procs.append(proc)

            for proc in procs:
                proc.join()

            with open(args.out_file, 'w') as writer:
                results = []
                for worker_idx in range(len(parameters)):
                    file = args.out_file + str(worker_idx)
                    with open(file, 'r') as reader:
                        for line in reader:
                            line = ujson.loads(line)
                            results.append(line)
                    os.remove(file)
                assert len(results) == count, (args.file, len(results), count)
                for line in results:
                    print(ujson.dumps(line), file=writer)


def evaluation(args):
    def load_records(file):
        with open(file, 'r') as reader:
            performances = [ujson.loads(line) for line in reader]
        return performances

    performances = load_records(file=args.out_file)
    history = PrettyTable([
        'Datatime', '#Rows', '#Equiv', '#NotEquiv', '#SynErr', f'#TimeOut({args.timeout})', '#NotSupErr',
        '#NotImplErr', '#Unknown', '#OtherErrs', '#Total', 'SuccessRate(%)', 'TotalTime(s)',
    ])

    for bound_size in range(1, 1 + args.bound_size):

        results = {
            '#Equiv': 0,
            '#NotEquiv': 0,
            '#SynErr': 0,
            '#TimeOut': 0,
            '#NotSupErr': 0,
            '#NotImplErr': 0,
            '#Unknown': 0,
            '#OtherErrs': 0,
            '#Total': 0,
            'SuccessRate(%)': 0,
            'TotalTime(s)': 0,
        }
        for query in performances:
            gt, case = query['pair']
            states, times = query['states'], query['times']
            state, time_cost = states[bound_size - 1], times[bound_size - 1]
            if state == STATE.EQUIV:
                results['#Equiv'] += 1
            else:
                if state == STATE.NON_EQUIV:
                    results['#NotEquiv'] += 1
                    # print([gt, case])
                elif state == STATE.TIMEOUT:
                    results['#TimeOut'] += 1
                    # print([gt, case])
                elif state == STATE.SYN_ERR:
                    results['#SynErr'] += 1
                    # print([gt, case])
                elif state == STATE.NOT_SUP_ERR:
                    results['#NotSupErr'] += 1
                    # print([gt, case])
                elif state == STATE.NOT_IMPL_ERR:
                    results['#NotImplErr'] += 1
                    # print([gt, case])
                elif state == STATE.UNKNOWN:
                    results['#Unknown'] += 1
                    # print([gt, case])
                elif state == STATE.OTHER_ERR:
                    results['#OtherErrs'] += 1
                    # print([gt, case])
                else:
                    # print(f'Unknown Error: {[gt, case]}')
                    raise NotImplementedError
            results['TotalTime(s)'] += time_cost

        results['#Total'] = len(performances)
        results['SuccessRate(%)'] = (results["#Equiv"] + results["#NotEquiv"]) / results['#Total']

        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        history.add_row([
            now, bound_size, f'{results["#Equiv"]:3,}', f'{results["#NotEquiv"]:3,}',
            f'{results["#SynErr"]:3,}', f'{results["#TimeOut"]:3,}', f'{results["#NotSupErr"]:3,}',
            f'{results["#NotImplErr"]:3,}', f'{results["#Unknown"]:3,}', f'{results["#OtherErrs"]:3,}',
            f'{results["#Total"]:3,}', f"{results['SuccessRate(%)']:.2%}", f'{results["TotalTime(s)"]:6.4f}',
        ])
    print(history)

    EQUIV, NON_EQUIV, NO_SUPP, TIME_OUT, TIME_COST = 0, 0, 0, 0, 0
    for prf in performances:
        state = prf['states'][0]
        time_cost = prf['times'][0]
        if state == STATE.TIMEOUT:
            TIME_OUT += 1
        elif state == STATE.NON_EQUIV:
            NON_EQUIV += 1
        elif state == STATE.EQUIV:
            for i, state in enumerate(prf['states'][1:], start=1):
                time_cost += prf['times'][i]
                if state == STATE.NON_EQUIV:
                    NON_EQUIV += 1
                    break
                elif state == STATE.TIMEOUT:
                    EQUIV += 1
                    break
                elif state == STATE.EQUIV:
                    pass
                else:
                    raise NotImplementedError(state)
            if state == STATE.EQUIV:
                EQUIV += 1
        else:
            NO_SUPP += 1
        TIME_COST += time_cost
    AVG_TIME_COST = round(TIME_COST / len(performances), 2)
    SUCCESS_RATE = (EQUIV + NON_EQUIV) / len(performances)
    print(
        f'#EQUIV: {EQUIV:3,}, #NON-EQUIV: {NON_EQUIV:3,}, #NOT-SUPP: {NO_SUPP:3,}, #TIMEOUT: {TIME_OUT:3,}, AvgTIME: {AVG_TIME_COST:.2f}s, SuccessRate: {SUCCESS_RATE:.2%}')


if __name__ == '__main__':
    # args.file = 'benchmark/calcite2/calcite2.jsonlines'
    # args.out_file = 'benchmark/calcite2/calcite2.out'
    # args.file = 'benchmark/literature/literature-rewrite.jsonlines'
    # args.out_file = 'benchmark/literature/literature-rewrite.out'
    # args.file = 'benchmark/leetcode/leetcode.jsonlines'
    # args.out_file = 'benchmark/leetcode/leetcode.out'
    print(args)
    if args.mode == 'train':
        train(args)
    elif args.mode == 'eval':
        evaluation(args)
    else:
        raise NotImplementedError
