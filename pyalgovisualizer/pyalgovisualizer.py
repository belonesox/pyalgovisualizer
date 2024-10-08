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
import tempfile
import dill

import matplotlib
import matplotlib.pyplot as plt
from copy import deepcopy, copy
matplotlib.use('cairo')
from pathlib import Path
from collections import deque
from functools import reduce

old_graph_cache = {}
old_cells_cache = {}
precision = 3

depends_on_line = False
current_python_filename = None
current_python_function = None
last_lines = deque()
current_python_function_state = ''
current_content_stem = ''
frame2state = {}

visualization_presuffix = ".visualization"
visualization_suffixes = ['.png', '.mp4']

visualization_stem = '.visualization'


back_functions = ['set_suspend', 'trace_dispatch'] 
ignore_functions = ['visualization', 'visme'] 

frame_name = None
import inspect

def set_current_python_filename(filename):
    global current_python_filename
    current_python_filename = filename


def set_color4cell(atable, i, j, color):
    if not atable:
        return
    if isinstance(i, str):
        i = get_row4label(atable, i)
    if isinstance(j, str):
        j = get_col4label(atable, j)

    # print('*'*10, i, j)
    for (row, col), cell in atable.get_celld().items():
        if row == i and col == j:
            cell.set_text_props(color=color)

def get_xy4cell(atable, i, j):
    if not atable:
        return

    bbox = atable.get_window_extent(renderer=atable.figure.canvas.get_renderer())
    bbox_fig = bbox.transformed(atable.axes.transAxes.inverted())        

    x = bbox_fig.x0
    y = bbox_fig.y0
    for (row, col), cell in atable.get_celld().items():
        if row > i and col == -1:
            y += cell._height      
        if row == i and col == j:
            x += cell._width/2
            y += cell._height/2      
        if row == 1 and col < j:
            if col == -1:
                ...
            x += cell._width      
    return (x, y)

def get_row4label(atable, label):
    if not atable:
        return
    label = str(label)
    for (row, col), cell in atable.get_celld().items():
        if col == -1:
            if cell.get_text().get_text() == label:
                return row
    return None            

def get_col4label(atable, label):
    if not atable:
        return
    label = str(label)
    for (row, col), cell in atable.get_celld().items():
        if row == 0:
            if cell.get_text().get_text() == label:
                return col
    return None            

def arrow(  table1, row_label1, col_label1,
            table2, row_label2, col_label2, color, linewidth=1):
    from matplotlib.patches import ConnectionPatch

    r1_ = row_label1
    if isinstance(row_label1, str):
        r1_ = get_row4label(table1, row_label1)
        if r1_ is None:
            print(f"row_label1={row_label1} not found")

    c1_ = col_label1
    if isinstance(col_label1, str):
        c1_ = get_col4label(table1, col_label1)
        if c1_ is None:
            print(f"col_label1={col_label1} not found")
    
    xy1 = get_xy4cell(table1, r1_, c1_)

    r2_ = row_label2
    if isinstance(row_label2, str):
        r2_ = get_row4label(table2, row_label2)
        if r2_ is None:
            print(f"row_label2={row_label2} not found")

    c2_ = col_label2
    if isinstance(col_label2, str):
        c2_ = get_col4label(table2, col_label2)
        if c2_ is None:
            print(f"col_label2={col_label2} not found")

    xy2 = get_xy4cell(table2, r2_, c2_)

    # print("Arrow!", xy1, xy2)
    con = ConnectionPatch(xyA=xy1, xyB=xy2, 
                    coordsA=table1.axes.transData, 
                    coordsB=table2.axes.transData,
                    color=color,
                    arrowstyle="<-", linewidth=linewidth)
    table1.figure.add_artist(con)                



def get_source_line4frame(frame):
    source = inspect.getsource(frame.f_code)
    line = source.split('\n')[frame.f_lineno-frame.f_code.co_firstlineno]
    return line


def get_current_line(idx):
    global last_lines
    if len(last_lines)>idx:
        return last_lines[idx]
    if len(last_lines)>0:
        return last_lines[0]
    return ''

def mhash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def default_visualization_func(frame):
    print('+' * 20)
    for var_ in frame.f_locals:
        value = frame.f_locals[var_]
        print(var_, '=>', type(value))
    print('-' * 20)

viscallbacks = {
    # 'default': default_visualization_func
}    


from collections import defaultdict
import networkx as nx

def draw_graph(G, pos, ax, node_color=None, node_size=None, node_shape=None, 
                edge_labels=None, edge_color=None, edge_width=None, font_size=None):
    '''
    Drawing graph with possibility of customizing 
    even node shapes
    '''
    if not node_color:
        node_color = defaultdict(lambda: 'lightblue')
    if not node_size:
        node_size = defaultdict(lambda: 250)
    if not node_shape:
        node_shape = defaultdict(lambda: 'o')    
    if not edge_color:
        edge_color = 'green'
    if not edge_width:
        edge_width = 0.4
    if not font_size:
        font_size = 8    

    for node in G.nodes():
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=[node],
            node_color=node_color[node],
            node_size=node_size[node],
            node_shape=node_shape[node],
            ax=ax
        )

    nx.draw_networkx_edges(
        G,
        pos,
        edge_color=edge_color,
        width=edge_width,
        ax=ax,
    )

    nx.draw_networkx_labels(G, pos, ax=ax)
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=font_size, ax=ax)
    ...


def tune_ax_for_table(ax_):
    ax_.set_axis_off() 
    ax_.get_xaxis().set_visible(False)
    ax_.get_yaxis().set_visible(False)


def tune_ax_for_graph(ax_):
    ax_.get_xaxis().set_visible(True)
    ax_.get_yaxis().set_visible(True)
    ax_.set_axis_on() 



def tune_axes_for_table(ax):
    plt.box(on=False)
    for ax_ in ax:
        tune_ax_for_table(ax_)

def tune_ax_for_grid(ax):
    ax.set_axis_on() 
    ax.get_xaxis().set_visible(True)
    ax.get_yaxis().set_visible(True)
    ax.grid(color='g', linestyle=':', linewidth=0.5)


def table_for_axn(axes, axn,  cellText, rowLabels, colLabels, offset_y=0, loc='center'):
    global old_cells_cache

    ax = axes[axn]
    bbox=None
    if offset_y:
        bbox=(0, offset_y, 1, 0.1)

    atable = ax.table(cellText=cellText,
                        rowLabels=rowLabels,
                        colLabels=colLabels,
                        rowColours=["aliceblue"]*len(rowLabels),
                        # cellColours=[["aliceblue"]*len(cellText[0])],
                        loc=loc,
                        bbox=bbox
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

def table4scalars(axes, axn, locals, varnames, offset_y=0, loc='center'):
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
                varnames, offset_y=offset_y, loc=loc)

# deprecated
table2scalars = table4scalars

def table4vectors(axes, axn, locals, varnames):
    data = []
    maxlen = 0
    if type(varnames) == str:
        varnames = varnames.split()


    list_ = [False] * len(varnames)
    for i_, var_ in enumerate(varnames):
        if var_ in locals:
            lv_ = locals[var_]
            if lv_ is None:
                lv_ = []
            if type(lv_)==list:
                list_[i_] = deepcopy(lv_)
            elif type(lv_) in [str, tuple, deque]:
                list_[i_] = list(lv_)
            elif type(lv_) in [set]:
                list_[i_] = sorted(list(lv_))
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


def table4matrix(axes, axn, A, title='', label_rows=None, label_cols=None):
    rows = 0
    A = deepcopy(A)
    if title: 
        axes[axn].set_title(title)
    if type(A) == list:
        rows = len(A)
        if rows == 0:
            return None
        cols = max([len(row) for row in A])
        if cols == 0:
            return None
        A = [list(row) + [''] * (cols - len(row)) for row in A]
    elif isinstance(A, dict):
        rows = len(A.keys())
        if not label_rows:
            label_rows = sorted(A.keys())
        if not label_cols:
            label_cols = sorted(reduce(set.union, [set(row.keys()) for row in A.values()] + [set()]))
        cols = len(label_cols)
        if cols == 0:
            return None
        A = [[A.get(row, {}).get(col, '') for col in label_cols] for row in label_rows]
    else:    
        rows = A.shape[0]
        cols = A.shape[1]
        A = np.round(A, 3)

    if not label_rows:
        label_rows = list(range(rows))

    if not label_cols:
        label_cols = list(range(cols))

    if min(rows, cols)==0:    
        return None

    return table_for_axn(axes, axn, 
                A, 
                label_rows, 
                label_cols)


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



from collections import deque
previous_vars = {}


def get_vars():
    # if not current_python_function:
    #     return None
    vars_ = frame2state[current_python_filename][current_python_function]['vars']
    return vars_    

def finish(scene, animations):
    if animations:
        mp4 = scene.file_writer.get_next_partial_movie_path()
        scene.play(*animations)
        shutil.copy(mp4, '.visualization.mp4')

def save(fig, algfilename=None, dpi=96):
    visualization_stem_  = visualization_stem
    if algfilename:
        visualization_stem_ = Path(algfilename).stem + visualization_stem_
    with tempfile.TemporaryDirectory() as tmp:
        deploy_ = Path(tmp) / (tempfile.gettempprefix() + '-visualization.png')
        prod_ = Path(current_python_filename).parent / (visualization_stem_ + ".png")    
        fig.savefig(deploy_, dpi=dpi)
        plt.close(fig)
        # print(f"Move {deploy_} to {prod_}")
        shutil.move(deploy_, prod_)

def remove_nonpickled(d):
    for k in list(d.keys()):
        try:
            if k in 'locs_' or not dill.pickles(d[k]):
                del d[k]
        except Exception as ex_:
            del d[k]
            print(f"*"*20)        
            print(f"{k} cannot be tested to pickle")        
            print(f"*"*20)        
            # raise(ex_)

def clone(toclone):
    '''
    Safe cloning what we can deepcopy,
    removing non-deepcopied stuff
    '''
    locals_ = copy(toclone)
    remove_non_deepcopied(locals_)    
    return deepcopy(locals_)


def remove_non_deepcopied(d):
    for k in list(d.keys()):
        try:
            _ = deepcopy(d[k])
        except Exception as ex_:
            del d[k]

def set_options(depends_on_line_=None):
    global depends_on_line
    if depends_on_line_ is not None:
        depends_on_line = depends_on_line_


def my_set_suspend(self, thread, stop_reason, suspend_other_threads=False, is_pause=False, original_step_cmd=-1):
    # print('*'*40)
    # print('my_set_suspend')
    # print('-'*40)
    info = set_additional_thread_info(thread)
    # print("thread.ident=>", thread.ident)
    curframe = inspect.currentframe().f_back
    while curframe:
        ignore = False
        for pat_ in back_functions:
            (filename, line_number, function_name, lines, index) = inspect.getframeinfo(curframe)        
            if pat_ in function_name:
                ignore = True
                break
        if not ignore:
            break 
        curframe = curframe.f_back

    if curframe:
        (filename, line_number, function_name, lines, index) = inspect.getframeinfo(curframe)        
        # print(filename, line_number, function_name)

        # print(filename, __file__)
        if not (filename == __file__ or 'pydev' in filename) and function_name not in ignore_functions:
            global current_python_filename 
            global current_python_function 
            global last_lines
            global frame2state

            current_python_filename = filename
            current_python_function = function_name

            if filename not in frame2state:
                hash_ = 'null'
                with open(filename) as lf:
                    hash_ = mhash(lf.read())
                frame2state[current_python_filename] = {
                    'hcode': hash_ 
                }
            if function_name not in frame2state[filename]:
                frame2state[filename][function_name] = {
                    'vars': deque()
                }
                # print('\n'.join(lines))

            #print("LOCALS ", locals_str)
            # locals_ = copy(curframe.f_locals)
            # remove_non_deepcopied(locals_)    
            copy_vars = clone(curframe.f_locals)
            previous_vars = frame2state[filename][function_name]['vars']
            # print('*'*20)
            # print(function_name)
            # print(copy_vars)
            # print('01'*30)
            # print(len(previous_vars))
            previous_vars.appendleft(copy_vars)
            if len(previous_vars)>3:
                previous_vars.pop()
            remove_nonpickled(copy_vars)    
            frame2state[filename][function_name]['hvars'] = hashlib.md5(dill.dumps(copy_vars)).hexdigest()

            current_content_stem = Path(filename).parent / '.cache' / Path(filename).name / frame2state[filename]['hcode'] / function_name  
            # print('08'*20)
            if depends_on_line:
                # print(f'depends_on_line={depends_on_line}')
                current_content_stem /= str(line_number)
                last_lines.appendleft('\n'.join(lines))
                if len(last_lines)>5:
                    last_lines.pop()

            current_content_stem /= frame2state[filename][function_name]['hvars']
            # print(current_content_stem)
            # print('09'*20)

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


















