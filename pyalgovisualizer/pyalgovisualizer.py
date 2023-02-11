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


# def default_visualization_func(frame):
#     print('+' * 20)
#     for var_ in frame.f_locals:
#         value = frame.f_locals[var_]
#         print(var_, '=>', type(value))
#     print('-' * 20)

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

def table_for_axn(axes, axn,  cellText, rowLabels, colLabels):
    global old_cells_cache
    print(old_cells_cache)

    ax = axes[axn]
    atable = ax.table(cellText=cellText,
                        rowLabels=rowLabels,
                        colLabels=colLabels,
                        loc='center',
                )
    atable.scale(1, 1.6) 

    cells_ = atable.get_celld()
    for key, cell in cells_.items():
        cell.set_linewidth(0.2)
        cell.set_linestyle("dotted")
        cell.set_text_props(ha="center")
        cell.set_text_props(backgroundcolor="white")
        if axn in old_cells_cache:
            old_text = old_cells_cache[axn][key].get_text().get_text()
            new_text = cell.get_text().get_text()
            if old_text != new_text:
                cell.set_text_props(backgroundcolor="yellow")

    old_cells_cache[axn] = deepcopy(cells_)
    return atable


def table2scalars(axes, axn, locals, varnames):
    data = []
    for var_ in varnames:
        if var_ in locals and locals[var_] is not None:
            data.append(str(locals[var_]))
        else:    
            data.append('')

    return table_for_axn(axes, axn, 
                [data], 
                ['value'], 
                varnames)


def table2vectors(axes, axn, locals, varnames):
    data = []
    maxlen = 0

    list_ = [False] * len(varnames)
    for i_, var_ in enumerate(varnames):
        if var_ in locals:
            if type(locals[var_])==list or type(locals[var_])==str:
                list_[i_] = list(locals[var_])
                maxlen = max(maxlen, len(locals[var_]))
    if maxlen == 0:
        return None        

    for i_, var_ in enumerate(varnames):
        if list_[i_]:
            data.append(list_[i_] + [''] * (maxlen  - len(locals[var_])))
        else:    
            data.append([''] * maxlen)

    return table_for_axn(axes, axn, 
                data, 
                varnames, 
                list(range(maxlen)))




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
        # print(viscallbacks.keys())
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


















