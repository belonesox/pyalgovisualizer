"""Main module."""

import sys
import pydevd
# from _pydevd_bundle.pydevd_thread_lifecycle import suspend_all_threads, mark_thread_suspended
from _pydevd_bundle.pydevd_additional_thread_info import set_additional_thread_info
import threading
import traceback      
import inspect
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from copy import deepcopy, copy
matplotlib.use('cairo')
from pathlib import Path

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

def tune_ax_for_grid(ax):
    ax.set_axis_on() 
    ax.get_xaxis().set_visible(True)
    ax.get_yaxis().set_visible(True)
    ax.grid(color='g', linestyle=':', linewidth=0.5)


def table_for_axn(axes, axn,  cellText, rowLabels, colLabels):
    global old_cells_cache

    ax = axes[axn]
    atable = ax.table(cellText=cellText,
                        rowLabels=rowLabels,
                        colLabels=colLabels,
                        rowColours=["aliceblue"]*len(rowLabels),
                        # cellColours=[["aliceblue"]*len(cellText[0])],
                        loc='center',
                )
    atable.scale(1, 1.6) 

    cells_ = atable.get_celld()
    for key, cell in cells_.items():
        cell.set_linewidth(0.2)
        cell.set_linestyle("dotted")
        cell.set_text_props(ha="center")
        if key[0] > 0 and key[1] > 0:
            cell.set_text_props(backgroundcolor="white")

        if key[0] == 0:
            # cell.set_text_props(backgroundcolor="#aaaaff")
            cell.set_facecolor("#bbbbff")            

        if axn in old_cells_cache:
            occ = old_cells_cache[axn]
            if key in occ:
                old_text = occ[key].get_text().get_text()
                new_text = cell.get_text().get_text()
                if old_text != new_text:
                    cell.set_text_props(backgroundcolor="yellow")

    old_cells_cache[axn] = copy(cells_)
    return atable


def table4scalars(axes, axn, locals, varnames):
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

# deprecated
table2scalars = table4scalars

def table4vectors(axes, axn, locals, varnames):
    data = []
    maxlen = 0

    list_ = [False] * len(varnames)
    for i_, var_ in enumerate(varnames):
        if var_ in locals:
            lv_ = locals[var_]
            if type(lv_)==list:
                list_[i_] = lv_
            elif type(lv_) in [str, tuple]:
                list_[i_] = list(lv_)
            elif type(lv_)==np.ndarray:
                list_[i_] = lv_.tolist()
            if list_[i_]:    
                maxlen = max(maxlen, len(list_[i_]))
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

# deprecated
table2vectors= table4vectors


def table4dicts(axes, axn, locals, varnames):
    data = []
    dict_ = [False] * len(varnames)
    all_keys = set()
    for i_, var_ in enumerate(varnames):
        if var_ in locals:
            lv_ = locals[var_]
            if isinstance(lv_, dict):
                dict_[i_] = lv_
            if dict_[i_]:    
                all_keys |= lv_.keys()

    all_keys_list = sorted(all_keys)

    if not all_keys_list:
        return None

    for i_, var_ in enumerate(varnames):
        if dict_[i_]:
            row = []
            for k in all_keys_list:
                if k in dict_[i_]:
                    row.append(dict_[i_][k])     
                else:
                    row.append('')
            data.append(row)
        else:    
            data.append([''] * len(all_keys_list))

    return table_for_axn(axes, axn, 
                data, 
                varnames, 
                all_keys_list)


def table2matrix(axes, axn, A):
    return table_for_axn(axes, axn, 
                A, 
                list(range(A.shape[0])), 
                list(range(A.shape[1])))



def vis_stack(nrows, **kwargs):
    # plt.subplots(nrows=nrows, ncols=1)
    fig, axes = plt.subplots(nrows=nrows, ncols=1, **kwargs)
    tune_axes_for_table(axes)
    return fig, axes


def any2csscolor(alist):
    import matplotlib.colors as mcolors
    pallete = mcolors.CSS4_COLORS
    ckeys = list(pallete.keys())
    unique = list(set(alist))
    val2id = dict([(v, k) for k, v in enumerate(unique)])

    colors_ = []
    for i_ in range(len(alist)):
        color_ = pallete[ckeys[val2id[alist[i_]] % len(ckeys)]]
        colors_.append(color_)
    return colors_    

def text4barh(ax, rects, texts):
    for i, rect in enumerate(rects):
        h_ = rect.get_height()
        w_ = rect.get_width()
        ax.text(rect.get_x() + w_ / 2.0, rect.get_y() + h_ / 2.0, 
                texts[i], ha='center', va='bottom')            





def save(fig, algfilename):
    fig.savefig(Path(algfilename).with_suffix(".visualization.png"), dpi=150)



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
                ignore = True
                break
        if not ignore:
            break 
        curframe = curframe.f_back
    
    if curframe:
        for k, v in viscallbacks.items():
            v(curframe)

    return original_set_suspend(self, thread, stop_reason, suspend_other_threads, is_pause, original_step_cmd)


pydevd.PyDB.set_suspend = my_set_suspend


















