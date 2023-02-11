"""Main module."""

import sys
import pydevd
# from _pydevd_bundle.pydevd_thread_lifecycle import suspend_all_threads, mark_thread_suspended
from _pydevd_bundle.pydevd_additional_thread_info import set_additional_thread_info
import threading
import traceback      
import inspect

import matplotlib
import matplotlib.pyplot as plt
from copy import deepcopy
matplotlib.use('cairo')

original_set_suspend = pydevd.PyDB.set_suspend

old_cells_cache = {}


def default_visualization_func(frame):
    print('+' * 20)
    for var_ in frame.f_locals:
        value = frame.f_locals[var_]
        print(var_, '=>', type(value))
    print('-' * 20)

viscallbacks = {
    # 'default': default_visualization_func
}    

def tune_ax_for_table(ax_):
    ax_.set_axis_off() 
    ax_.get_xaxis().set_visible(False)
    ax_.get_yaxis().set_visible(False)

def tune_axes_for_table(ax):
    plt.box(on=False)
    for ax_ in ax:
        tune_ax_for_table(ax_)



def my_set_suspend(self, thread, stop_reason, suspend_other_threads=False, is_pause=False, original_step_cmd=-1):
    # print('*'*40)
    # print('my_set_suspend')
    # print('-'*40)
    info = set_additional_thread_info(thread)
    # print("thread.ident=>", thread.ident)
    curframe = inspect.currentframe().f_back
    ignore_functions = ['set_suspend', 'trace_dispatch', 'visualization'] 
    while curframe:
        ignore = False
        for pat_ in ignore_functions:
            (filename, line_number, function_name, lines, index) = inspect.getframeinfo(curframe)        
            if pat_ in function_name:
                # print('ignored', function_name)
                ignore = True
                break
        if not ignore:
            # print('ok', function_name)
            break 
        curframe = curframe.f_back
    
    if curframe:
        print(viscallbacks.keys())
        for k, v in viscallbacks.items():
            v(curframe)

    # traceback.print_stack(curframe)

    #     if 'filename'

    # frame_ = sys._current_frames()[thread.ident]
    # breakpoint()
    # print(frame_)
    # traceback.print_stack(frame_)
    # for th in threading.enumerate():
    #     print("th=", th)
    #     # traceback.print_stack(sys._current_frames()[th.ident])
    #     print()

    # frame = info.get_topmost_frame(thread)
    # if frame is not None:
    #     print('111111')
    #     print('+' * 20)
    #     print(dir(frame))
    #     for var_ in frame.f_locals:
    #         value = frame.f_locals[var_]
    #         print(var_, '=>', type(value))
    #     # for var_ in frame.f_locals:
    #     #     value = frame.f_locals[var_]
    #     #     print(var_, '=>', value)
    #     print('-' * 20)

        # default_visualization(frame)
    return original_set_suspend(self, thread, stop_reason, suspend_other_threads, is_pause, original_step_cmd)


pydevd.PyDB.set_suspend = my_set_suspend


























# import ctypes.util
# original_find_library = ctypes.util.find_library

# def our_find_library(name):
#     libname = f'lib{name}.so'
#     return libname

# ctypes.util.find_library = our_find_library


# def  our_popen(scmd):
#     print('Fake!!!')
#     pass

# preloadso_ = []          
# LIBDIR = '/lib/x86_64-linux-gnu'  
# ok_ = False


# for LIBDIR in ['/lib64', '/lib/x86_64-linux-gnu', '/lib']:
#     if os.path.exists(LIBDIR):
#         for file_ in os.listdir(LIBDIR):
#             filep_ = os.path.join(LIBDIR, file_)
#             # print(file_)
#             if '.so' in file_ and not os.path.islink(filep_) and not 'libthread_db' in file_ and os.path.getsize(filep_)>1024:
#                 okl_ = False
#                 # for start_ in ['lib']:
#                 for start_ in ['libc-', #'libdl-', #'libcap'
#                               ]:
#                     okl_ = okl_ or file_.startswith(start_) and not 'libc-client' in file_
#                     if okl_:
#                         break
#                 if okl_:            
#                     preloadso_.append(filep_)
#                     ok_ = True    
#     if ok_:
#         break                

# LDSO_HOST = ''
# for p_ in ['/lib64/ld-linux-x86-64.so.2']:
#     if os.path.exists(p_):
#         LDSO_HOST = p_     
#         break

# LD_LIBRARY_PATH = ''
# if 'LD_LIBRARY_PATH' in os.environ: 
#     LD_LIBRARY_PATH = os.environ['LD_LIBRARY_PATH'] 

# root_dir = None
# dirs_ = ['ebin', 'pbin']
# for dir_name in dirs_:
#     if dir_name in sys.executable:
#         root_dir = sys.executable.split(dir_name)[0]
#         break
#     if dir_name in sys.argv[0]:
#         root_dir = sys.argv[0].split(dir_name)[0]
#         break


# class TerraPopen(subprocess.Popen):
#     """ Execute a child program in a new process.

#     For a complete description of the arguments see the Python documentation.

#     Arguments:
#       args: A string, or a sequence of program arguments.

#       bufsize: supplied as the buffering argument to the open() function when
#           creating the stdin/stdout/stderr pipe file objects

#       executable: A replacement program to execute.

#       stdin, stdout and stderr: These specify the executed programs' standard
#           input, standard output and standard error file handles, respectively.

#       preexec_fn: (POSIX only) An object to be called in the child process
#           just before the child is executed.

#       close_fds: Controls closing or inheriting of file descriptors.

#       shell: If true, the command will be executed through the shell.

#       cwd: Sets the current directory before the child is executed.

#       env: Defines the environment variables for the new process.

#       text: If true, decode stdin, stdout and stderr using the given encoding
#           (if set) or the system default otherwise.

#       universal_newlines: Alias of text, provided for backwards compatibility.

#       startupinfo and creationflags (Windows only)

#       restore_signals (POSIX only)

#       start_new_session (POSIX only)

#       pass_fds (POSIX only)

#       encoding and errors: Text mode encoding and error handling to use for
#           file objects stdin, stdout and stderr.

#     Attributes:
#         stdin, stdout, stderr, pid, returncode
#     """
#     _child_created = False  # Set here since __del__ checks it

#     def __init__(self, args, **kwargs):
#         args_ = None
#         args_is_str = isinstance(args, str)
#         # print("@"*10, args)
#         if args_is_str:
#             args_ = list(args.split())
#         else:    
#             args_ = list(args)
#         # print("+"*10, args_)

#         # breakpoint()
#         if root_dir:
#             ldso = os.path.join(root_dir, 'pbin', 'ld.so')
#             utterms_ = os.path.split(args_[0])
#             # print(utterms_)
#             utname = utterms_[-1]
#             pbin_path = os.path.join(root_dir, 'pbin', utname)
#             ebin_path = os.path.join(root_dir, 'ebin', utname)
#             os.environ['LD_PRELOAD'] = ''
#             os.environ['LD_PRELOAD_PATH'] = ''
#             os.environ['LD_LIBRARY_PATH'] = LD_LIBRARY_PATH
#             os.environ['LD_LIBRARY_PATH'] += ':' + os.path.join(root_dir, 'pbin') + ':' + os.path.join(root_dir, 'lib64')
#             if os.path.exists(pbin_path) and not os.path.exists(ebin_path):
#                 args_[0] = pbin_path
#             else:
#                 # Here we should 
#                 if utterms_[0] == '':
#                     if os.path.exists(ebin_path):
#                         args_[0] = ebin_path
#                     else:    
#                         utname_ = shutil.which(utname)
#                         # print(utname, '*'*20, utname_)
#                         if utname_:
#                             args_[0] = utname_

#                 header = open(args_[0], "rb").read(32)     
#                 if not b'ELF' in header:
#                     interpreter = '/bin/sh'
#                     shebang_start = b'#!'
#                     if header.startswith(shebang_start):
#                         headerline = header.split(b'\n')[0][len(shebang_start):]
#                         for terms_ in reversed(headerline.split()):
#                             args_.insert(0, terms_)    
#                     else:    
#                         args_.insert(0, interpreter)    
#                 ldso = LDSO_HOST     
#                 os.environ['LD_PRELOAD_PATH'] = LIBDIR
#                 # os.environ['LD_LIBRARY_PATH'] = ''
#                 os.environ['LD_LIBRARY_PATH'] = ':'.join([LIBDIR, '/usr/lib64', '/usr/lib/x86_64-linux-gnu/', LD_LIBRARY_PATH])
#                 os.environ['LD_PRELOAD']=' '.join(preloadso_)
#                 os.environ['PYTHONPATH']=''
#                 # print("os.environ['LD_PRELOAD']", os.environ['LD_PRELOAD'])
#                 # print("os.environ['LD_PRELOAD_PATH']", os.environ['LD_PRELOAD_PATH'])
#                 # print('*****')
#             # args_.insert(0, '/bin/sh')    
#             args_.insert(0, ldso)    

#         # time.sleep(5)
#         # print("!"*10, args_)
#         if args_is_str:
#             args_ = " ".join(args_)

#         # for k, v in os.environ.items():
#         #     print(f'{k}={v}')
#         # # print(list(dict(os.environ).items()))
#         # print(args_)
#         super().__init__(args_, **kwargs)
#         pass


# subprocess.Popen=TerraPopen
