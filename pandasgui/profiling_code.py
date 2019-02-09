# region PROFILING CODE ############
import inspect
import sys
import time
import functools
import colorama
from colorama import Fore, Style

INCLUDE_FAST_LINES = False
glob_call_time_stack = []


def cprint(*args):
    sargs = [str(arg) for arg in args]
    print(Fore.RED + ' '.join(sargs) + Style.RESET_ALL)


def tracefunc(frame, event, arg,
              indent=[0], filename=__file__, call_time_stack=glob_call_time_stack, last_line_num=[None],
              last_line_start=[None]):
    if (frame.f_code.co_filename == filename):
        if event == "call":
            call_time_stack.append(time.time())
            indent[0] += 3
            cprint("-" * indent[0] + "> call function", frame.f_code.co_name)
        elif event == "return":
            cprint("<" + "-" * indent[0], "exit function", frame.f_code.co_name,
                   f"({time.time() - call_time_stack.pop():.2f})")
            indent[0] -= 3
        if event == 'line':
            this_line_start = time.time()
            this_line_num = frame.f_lineno

            if last_line_num[0] is not None:
                last_line_duration = this_line_start - last_line_start[0]
                if INCLUDE_FAST_LINES or last_line_duration > 0.05:
                    cprint("Line {} took {:.2f}s".format(last_line_num[0], last_line_duration))

            last_line_start[0] = this_line_start
            last_line_num[0] = this_line_num
    return tracefunc


profiling_enabled = True
if profiling_enabled:
    sys.settrace(tracefunc)
# endregion ##########################
