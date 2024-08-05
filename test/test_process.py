# -*- coding:utf-8 -*-

import time
from multiprocessing import Process, Queue

from constants import STATE
from environment import Environment
from errors import *


def run(ROW_NUM=2):
    sql1, sql2 = [
        "SELECT USER_ID FROM ACTIONS",
        "SELECT USER_ID FROM ACTIONS",
    ]
    schema = {"ACTIONS": {"USER_ID": "INT", "POST_ID": "INT", "ACTION_DATE": "DATE",
                          "ACTION": "ENUM,VIEW,LIKE,REACTION,COMMENT,REPORT,SHARE", "EXTRA": "ENUM,SPAM,RACISM,NULL"},
              "REMOVALS": {"POST_ID": "INT", "REMOVE_DATE": "DATE"}}
    constraints = [{"int": {"value": "ACTIONS__USER_ID"}}, {"int": {"value": "ACTIONS__POST_ID"}},
                   {"int": {"value": "ACTIONS__ACTION_DATE"}}, {"int": {"value": "ACTIONS__ACTION"}},
                   {"int": {"value": "ACTIONS__EXTRA"}}, {"int": {"value": "REMOVALS__POST_ID"}},
                   {"primary": [{"value": "REMOVALS__POST_ID"}]}, {"int": {"value": "REMOVALS__REMOVE_DATE"}}, {
                       "in": [{"value": "ACTIONS__ACTION"},
                              [{"literal": "VIEW"}, {"literal": "LIKE"}, {"literal": "REACTION"},
                               {"literal": "COMMENT"}, {"literal": "REPORT"}, {"literal": "SHARE"}]]},
                   {"foreign": [{"value": "REMOVALS__POST_ID"}, {"value": "ACTIONS__POST_ID"}]}]

    with Environment(verbose=True, timer=True) as env:
        for k, v in schema.items():
            env.create_database(attributes=list(v.keys()), bound_size=ROW_NUM, name=k)
        env.add_constraints(constraints)
        env.save_checkpoints()
        if env._script_writer is not None:
            env._script_writer.save_checkpoints()
        result = env.analyze(sql1, sql2, out_file="test/test.py")
    return result


def _f(queue: Queue):
    start_time = time.perf_counter()
    try:
        result = run()
        if result == False:
            raise NotEquivalenceError()
        else:
            state = STATE.EQUIV
    except SyntaxError as err:
        state = STATE.SYN_ERR
    except NotEquivalenceError as err:
        state = STATE.NON_EQUIV
    except TimeoutError as err:
        state = STATE.TIMEOUT
    except NotSupportedError as err:
        state = STATE.NOT_SUP_ERR
    except UnknownError as err:
        state = STATE.UNKNOWN
    except NotImplementedError as err:
        state = STATE.NOT_IMPL_ERR
    except Exception as err:
        state = STATE.OTHER_ERR
    end_time = time.perf_counter()
    time_cost = round(end_time - start_time, 6)
    if time_cost > 60:
        state = STATE.TIMEOUT
    queue.put([state, time_cost])


def main():
    queue = Queue()

    proc = Process(target=_f, args=(queue,))
    proc.start()

    TIMEOUT = 10
    start = time.time()
    while time.time() - start <= TIMEOUT:
        if not proc.is_alive():
            # All the processes are done, break now.
            break

        time.sleep(.1)  # Just to avoid hogging the CPU
    else:
        # We only enter this if we didn't 'break' above.
        print("timed out, killing all processes")
        proc.terminate()
        proc.join()
        return

    results = queue.get()
    print(results)


if __name__ == '__main__':
    main()
