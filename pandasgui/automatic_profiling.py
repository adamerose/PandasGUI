def enable_profiling(glob_call_time_stack=[]):
    import sys
    import inspect
    import os
    import time

    def tracefunc(frame, event, arg,
                  indent=[0], filename=__file__, call_time_stack=glob_call_time_stack, last_line_num=[None],
                  last_line_start=[None]):
        '''
        frame: See frame in table https://docs.python.org/3/library/inspect.html#types-and-members
        event: https://docs.python.org/3/library/inspect.html#types-and-members
        arg: For 'return' event, arg is return value.
             For 'exception' event, arg is (exception, value, traceback).
             Otherwise arg is None
        '''
        global TRACEFUNC_PROJECT_FILES
        if 'TRACEFUNC_PROJECT_FILES' not in globals():
            caller_file = inspect.currentframe().f_code.co_filename
            dirname = os.path.dirname(caller_file)
            # Find project root path
            while True:
                if '__init__.py' in os.listdir(dirname):
                    project_root = dirname
                    break
                elif os.path.dirname(dirname) == dirname:
                    # Got to drive root without __init__ file so project root is just the folder containing the caller file
                    project_root = os.path.dirname(caller_file)
                    break
                dirname = os.path.dirname(dirname)

            TRACEFUNC_PROJECT_FILES = []
            for root, subFolder, files in os.walk(project_root):
                for item in files:
                    if item.endswith(".py"):
                        path = str(os.path.join(root, item)).replace('\\', '/')
                        TRACEFUNC_PROJECT_FILES.append(path)

        line = frame.f_lineno
        file_path = frame.f_code.co_filename
        file_name = os.path.basename(file_path)
        object_name = frame.f_code.co_name

        if file_path in TRACEFUNC_PROJECT_FILES:
            if event == "call":
                call_time_stack.append(time.time())
                indent[0] += 3
                print("-" * indent[0] + f"> call function {frame.f_code.co_name} [Line {frame.f_lineno}]")
            elif event == "return":
                print("<" + "-" * indent[0], "exit function", frame.f_code.co_name,
                      f"({time.time() - call_time_stack.pop():.2f}s)")
                indent[0] -= 3
            if event == 'line':
                this_line_start = time.time()
                this_line_num = frame.f_lineno
        return tracefunc

    sys.settrace(tracefunc)
