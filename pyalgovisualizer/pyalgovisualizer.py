"""Main module."""

import sys

original_set_suspend = None
if 'debugpy' in sys.modules:
    import pydevd
    from _pydevd_bundle.pydevd_additional_thread_info import set_additional_thread_info
    original_set_suspend = pydevd.PyDB.set_suspend

import threading
import traceback      
import shutil
import inspect
import numpy as np
import hashlib
import dill

import matplotlib
import matplotlib.pyplot as plt
from copy import deepcopy, copy
matplotlib.use('cairo')
from pathlib import Path

old_graph_cache = {}
old_cells_cache = {}
precision = 3

visualization_stem = '.visualization'

frame_name = None
import inspect

def mhash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

# def register(params):
#     global frame_name
   
#     params_str = str(vars(params))
#     modelname = mhash(inspect.getsource(define_model)) +  '-' + mhash(params_str)
#     # params_str = pprint.pformat(vars(params), indent=4)
#     # with open('params.txt', 'w', encoding='utf-8') as lf:
#     #     lf.write(params_str)
#     model_file = modeldbpath / (modelname + '.model')
#     print(f'Working with model {modelname}')
#     if model_file.exists():
#         with open(model_file, mode='rb') as file:
#             model = cloudpickle.load(file)        
#             return model
#     ttc.tic()
#     m = ConcreteModel()
#     def save():
#         with open(model_file, mode='wb') as file:
#             cloudpickle.dump(m, file)

#     m.__dict__.update(params.__dict__)




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

def value2str(v):
    if v and isinstance(v, tuple):
        s_ = []
        for v_ in v:
            s_.append(value2str(v_))  
        return ', '.join(s_)    
    if v and isinstance(v, float):
        return "{:0.3f}".format(v) 
    return str(v)

def table4scalars(axes, axn, locals, varnames):
    if type(varnames) == str:
        varnames = varnames.split()
    data = []
    for var_ in varnames:
        if var_ in locals and locals[var_] is not None:
            v = value2str(locals[var_])
            data.append(v)
        else:    
            data.append('')

    return table_for_axn(axes, axn, 
                [data], 
                ['value'], 
                varnames)

# deprecated
table2scalars = table4scalars

from collections import deque
def table4vectors(axes, axn, locals, varnames):
    data = []
    maxlen = 0
    if type(varnames) == str:
        varnames = varnames.split()


    list_ = [False] * len(varnames)
    for i_, var_ in enumerate(varnames):
        if var_ in locals:
            lv_ = locals[var_]
            if type(lv_)==list:
                list_[i_] = deepcopy(lv_)
            elif type(lv_) in [str, tuple, deque]:
                list_[i_] = list(lv_)
            elif type(lv_).__module__ in ['itertools']:
                list_[i_] = list(lv_)
            elif type(lv_)==np.ndarray:
                list_[i_] = lv_.tolist()
            if list_[i_]:    
                maxlen = max(maxlen, len(list_[i_]))

            for j_, v in enumerate(list_[i_]):
                list_[i_][j_] = value2str(v)

    if maxlen == 0:
        return None        

    for i_, var_ in enumerate(varnames):
        if list_[i_]:
            data.append(list_[i_] + [''] * (maxlen  - len(list_[i_])))
        else:    
            data.append([''] * maxlen)

    return table_for_axn(axes, axn, 
                data, 
                varnames, 
                list(range(maxlen)))

# deprecated
table2vectors= table4vectors


def table4dicts(axes, axn, locals, varnames):
    if type(varnames) == str:
        varnames = varnames.split()
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


def table4matrix(axes, axn, A, title=''):
    rows = 0
    A = deepcopy(A)
    if title: 
        axes[axn].set_title(title)
    if type(A) == list:
        rows = len(A)
        cols = max([len(row) for row in A])
        if cols == 0:
            return None
        A = [list(row) + [''] * (cols - len(row)) for row in A]
    else:    
        rows = len(A.shape[0])
        cols = len(A.shape[1])

    if min(rows, cols)==0:    
        return None

    return table_for_axn(axes, axn, 
                A, 
                list(range(rows)), 
                list(range(cols)))



def vis_stack(nrows, **kwargs):
    # plt.subplots(nrows=nrows, ncols=1)
    fig, axes = plt.subplots(nrows=nrows, ncols=1, **kwargs)
    tune_axes_for_table(axes)
    return fig, axes


def int2csscolor(intid):
    import matplotlib.colors as mcolors
    pallete = mcolors.CSS4_COLORS
    ckeys = list(pallete.keys())
    color_ = pallete[ckeys[intid % len(ckeys)]]
    return color_    

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





current_python_filename = None
current_python_function = None
current_python_function_state = ''
current_content_stem = ''
frame2state = {}

visualization_presuffix = ".visualization"
visualization_suffixes = ['.png', '.mp4']


def save(fig, algfilename=None, dpi=96):
    visualization_stem_  = visualization_stem
    if algfilename:
        visualization_stem_ = Path(algfilename).stem + visualization_stem_
    fig.savefig(Path(current_python_filename).parent / (visualization_stem_ + ".png"), dpi=dpi)
    plt.close(fig)

import pprint

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
        (filename, line_number, function_name, lines, index) = inspect.getframeinfo(curframe)        
        global current_python_filename 
        global current_python_function 
        global frame2state

        current_python_filename = filename
        current_python_function = function_name

        if filename not in frame2state:
            frame2state[current_python_filename] = {}
        if function_name not in frame2state[filename]:
            frame2state[filename][function_name] = {
                'hcode': mhash('\n'.join(lines))
            }

        #locals_str = pprint.pformat(curframe.f_locals, indent=4)

        #print("LOCALS ", locals_str)
        frame2state[filename][function_name]['hvars'] = hashlib.md5(dill.dumps(copy(curframe.f_locals))).hexdigest()
        #mhash(locals_str)

        current_content_stem = Path(filename).parent / '.cache' / Path(filename).name / function_name / frame2state[filename][function_name]['hcode']  / frame2state[filename][function_name]['hvars']

        found = False
        for suffix in visualization_suffixes:
            cache_file = current_content_stem.with_suffix(suffix)
            vis_file = Path(filename).parent / (visualization_stem + suffix)
            if cache_file.exists():
                shutil.copy(cache_file, vis_file)
                found = True
                # print(f"Found for {cache_file}!")

        if not found:
            for k, v in viscallbacks.items():
                v(curframe)
            for suffix in visualization_suffixes:
                cache_file = current_content_stem.with_suffix(suffix)
                vis_file = Path(filename).parent / (visualization_stem + suffix)
                if vis_file.exists():
                    # print(f"Copy {vis_file} to {cache_file}")
                    cache_file.parent.mkdir(exist_ok=True, parents=True)
                    shutil.copy(vis_file, cache_file)

    return original_set_suspend(self, thread, stop_reason, suspend_other_threads, is_pause, original_step_cmd)



if 'debugpy' in sys.modules:
    pydevd.PyDB.set_suspend = my_set_suspend


















