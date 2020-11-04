def automatic_profiling():
    import inspect
    import sys
    import time
    import functools

    INCLUDE_FAST_LINES = False
    glob_call_time_stack = []

    def tracefunc(frame, event, arg,
                  indent=[0], filename=__file__, call_time_stack=glob_call_time_stack, last_line_num=[None],
                  last_line_start=[None]):
        if (frame.f_code.co_filename == filename):
            if event == "call":
                call_time_stack.append(time.time())
                indent[0] += 3
                print("-" * indent[0] + "> call function", frame.f_code.co_name)
            elif event == "return":
                print("<" + "-" * indent[0], "exit function", frame.f_code.co_name,
                       f"({time.time() - call_time_stack.pop():.2f})")
                indent[0] -= 3
            if event == 'line':
                this_line_start = time.time()
                this_line_num = frame.f_lineno

                if last_line_num[0] is not None:
                    last_line_duration = this_line_start - last_line_start[0]
                    if INCLUDE_FAST_LINES or last_line_duration > 0.05:
                        print("Line {} took {:.2f}s".format(last_line_num[0], last_line_duration))

                last_line_start[0] = this_line_start
                last_line_num[0] = this_line_num
        return tracefunc

    sys.settrace(tracefunc)