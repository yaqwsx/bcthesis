#! /usr/bin/env python

import sys, csv
from functools import partial

def prepare_csv(file):
    l = list(csv.reader(file))
    if l[0][0].startswith("sep"):
        return l[1], l[2:]
    return l[0], l[1:]

def get_mapping(header):
    res = {}
    for item, index in zip(header, range(0, len(header))):
        res[item] = index
    return res

def get_item(mapping, l, field):
    return l[mapping[field]]

def set_item(mapping, l, field, value):
    l[mapping[field]] = value

def filter_left_error(l, r):
    res = [(x, y) for x, y in zip(l, r) if get(x, "Note") in ["TIMEOUT", ""]]
    res = [list(t) for t in zip(*res)]
    return res[0], res[1]

def filter_left_timeout(l, r):
    res = [(x, y) for x, y in zip(l, r) if get(x, "Note") != "TIMEOUT"]
    res = [list(t) for t in zip(*res)]
    return res[0], res[1]

def filter_name_prefix(l, r, pref):
    res = [(x, y) for x, y in zip(l, r) if not get(x, "name").startswith(pref)]
    res = [list(t) for t in zip(*res)]
    return res[0], res[1]

def filter_no_equal(l, r):
    res = [(x, y) for x, y in zip(l, r) if get(y, "SMT calls Subseteq()") != 0]
    res = [list(t) for t in zip(*res)]
    return res[0], res[1]

def column_to_float(l, column, default=None):
    res = []
    for x in l:
        if (get(x, column) in ["None", ""]):
            set(x, column, default)
        else:
            set(x, column, float(get(x, column)))
        res.append(x)
    return res

def column_to_int(l, column, default=None):
    res = []
    for x in l:
        if (get(x, column) in ["None", ""]):
            set(x, column, default)
        else:
            set(x, column, int(get(x, column)))
        res.append(x)
    return res

def none_pass(l):
    res = []
    for x in l:
        if (get(x, "time") == "None"):
            set(x, "time", None)
        res.append(x)
    return res

def timeout_to_val(l, val):
    res = []
    for x in l:
        if (not get(x, "time")):
            set(x, "time", val)
        res.append(x)
    return res

def none_op(a, b, f, val = None):
    if a is None or b is None:
        return val
    return f(a, b)

def check_validity(l, r):
    for x, y in zip(l, r):
        if get(x, "name") != get(y, "name"):
            return False
    return True

def prepare_data(no_cache, cache):
    # no_cache, cache = filter_left_error(no_cache, cache)
    # cache, no_cache = filter_left_error(cache, no_cache)
    # cache, no_cache = filter_left_timeout(cache, no_cache)

    # cache, no_cache = filter_name_prefix(cache, no_cache, "jain")

    cache = column_to_float(cache, "time")
    no_cache = column_to_float(no_cache, "time")

    cache = column_to_int(cache, "SMT calls Subseteq()", 0)
    no_cache = column_to_int(no_cache, "SMT calls Subseteq()")
    cache = column_to_int(cache, "SMT subseteq on syntax. equal", 0)
    no_cache = column_to_int(no_cache, "SMT subseteq on syntax. equal", 0)
    cache = column_to_int(cache, "Hit count", 0)
    cache = column_to_int(cache, "Miss count", 0)

    # cache = timeout_to_val(cache, 240)
    # no_cache = timeout_to_val(no_cache, 240)

    return no_cache, cache

def table_header(s):
    return s

def table_header_r(s):
    return "\\mcrot{1}{l}{60}{" + table_header(s) + "}"

def tex_join_lines(a, b):
    return "\\pbox{20cm}{" + a + " \\\\ " + b + "}"

def tex_math(s):
    return str(s)
    return "$" + str(s) + "$"



with open(sys.argv[1], "rb") as first_file, open(sys.argv[2], "rb") as second_file:
    header, no_cache = prepare_csv(first_file)
    _, cache = prepare_csv(second_file)
    get = partial(get_item, get_mapping(header))
    set = partial(set_item, get_mapping(header))

# print(header)
# print("\n")

no_cache, cache = prepare_data(no_cache, cache)

# Print rm query
names = map(lambda x : get(x, "name"), no_cache)
# print("rm !({0})\n\n".format('|'.join(names)))

no_cache, cache = filter_no_equal(no_cache, cache)

if not check_validity(cache, no_cache):
    print("Names does not match!")
    sys.exit(1)

res_header = ["name", "states", "instructions", "cache_time", "no_cache_time",
    "difference", "percent", "Equal queries", "NC Solver calls", "C Solver calls"]
res = []
for nc, c in zip(no_cache, cache):
    res.append([
        get(nc, "name"),
        get(c, "states"),
        get(c, "Instruction executed"),
        get(c, "time"),
        get(nc, "time"),
        get(c, "time") - get(nc, "time"),
        get(c, "time") / get(nc, "time") - 1,
        get(c, "SMT calls Subseteq()"),
        none_op(get(nc, "SMT calls Subseteq()"), get(nc, "SMT subseteq on syntax. equal"), lambda x,y: x - y, "Unknown"),
        get(c, "Miss count")])

res = sorted(res, key = lambda x: x[0])

with open("_res.csv", "wb") as f:
    f.write("sep=,\n")
    cc = csv.writer(f)
    cc.writerow(res_header)
    cc.writerows(res)

with open("table.tex", "w") as f:
    f.write("\\begin{landscape}\n\t\\begin{longtable}{l@{\\hskip 0.5cm}rrrrrrrrR{1.5cm}}\n")

    # Header
    header = [table_header("Benchmark name"),
              table_header_r("Multi-states"),
              table_header_r(tex_join_lines("Instructions", "executed")),
              table_header_r(tex_join_lines("Time without", "caching [s]")),
              table_header_r(tex_join_lines("Time with", "caching [s]")),
              table_header_r(tex_join_lines("Time", "difference [s]")),
              table_header_r(tex_join_lines("Percentage", "difference")),
              table_header_r("Equal queries"),
              table_header_r(tex_join_lines("Solver calls", "without cache")),
              table_header_r(tex_join_lines("Solver calls", "with cache"))]

    f.write("\t\t\t\\caption{\\tablecaption}\\label{\\tablelabel}\\\\\n");
    f.write("\t\t\t" + " & ".join(header) + " \\\\\n")
    f.write("\t\t\t\\toprule\n")
    f.write("\t\t\t\\endfirsthead\n\n")

    f.write("\t\t\t\\caption*{\\textbf{Continued:}~\\tablecaptioncont}\\\\\n");
    f.write("\t\t\t" + " & ".join(header) + " \\\\\n")
    f.write("\t\t\t\\toprule\n")
    f.write("\t\t\t\\endhead\n\n")

    f.write("\t\t\t\\multicolumn{10}{c}{\\textit{Continue...}}\\\\\n")
    f.write("\t\t\t\\label{\\tablelabel}\n")
    f.write("\t\t\t\\endfoot\n")

    f.write("\t\t\t\\bottomrule\n")
    f.write("\t\t\t\\endlastfoot\n\n")

    c_time = 0
    nc_time = 0
    t_diff = 0
    eq = 0
    nc_solv = 0
    c_solv = 0
    for x, next in zip(res, res[1:] + [[res[-1][0]]]):
        c_time += x[3]
        nc_time += x[4]
        t_diff += x[5]
        eq += x[7]
        nc_solv += x[8]
        c_solv += x[9]

        now = x[0]
        x[0] = x[0].replace("bug02_sum01_bug02", "b2s1b2")
        x[0] = x[0].replace("__tTflag_arr_one_loop", "s_f_ol")
        x[0] = x[0].replace("unreach-call", "uc")
        x[0] = x[0].replace("_", "\\_")[:-3]
        x[1] = tex_math(x[1])
        x[2] = tex_math(x[2])
        x[3] = tex_math("\\SI{{{:.1f}}}{{}}".format(x[3]))
        x[4] = tex_math("\\SI{{{:.1f}}}{{}}".format(x[4]))
        x[5] = tex_math("\\SI{{{:.1f}}}{{}}".format(x[5]))
        x[3], x[4] = x[4], x[3]
        x[6] = tex_math("\\SI{{{:.1f}}}{{\percent}}".format(x[6] * 100))
        x[7] = tex_math(x[7])
        x[8] = tex_math(x[8])
        x[9] = tex_math(x[9])

        f.write("\t\t\t" + " & ".join(x) + " \\\\")
        if now[:-5] != next[0][:-5]:
            f.write("\\midrule")
        f.write("\n")

    summary = ["\\textbf{Summary}",
               "",
               "",
               tex_math("\\SI{{{:.1f}}}{{}}".format(nc_time)),
               tex_math("\\SI{{{:.1f}}}{{}}".format(c_time)),
               tex_math("\\SI{{{:.1f}}}{{}}".format(t_diff)),
               tex_math("\\SI{{{:.1f}}}{{\percent}}".format((c_time / nc_time - 1) * 100)),
               str(eq),
               str(nc_solv),
               str(c_solv)]
    f.write("\t\t\t\\bottomrule\n")
    f.write("\t\t\t" + " & ".join(summary) + " \\\\\n")
    

    f.write("\t\\end{longtable}\n\\end{landscape}\n")

# GNU plot data set
no_cache_set = [get(x, "time") for x in no_cache]
no_cache_set.sort()

cache_set = [get(x, "time") for x in cache]
cache_set.sort()

with open("_cache_plot.txt", "wb") as f:
    for x, y in zip(cache_set, range(1, len(cache_set) + 1)):
        f.write("{0}\t{1}\n".format(y, x))

with open("_no_cache_plot.txt", "wb") as f:
    for x, y in zip(no_cache_set, range(1, len(no_cache_set) + 1)):
        f.write("{0}\t{1}\n".format(y, x))

with open("_no_cache.csv", "wb") as first_file, open("_cache.csv", "wb") as second_file:
    first_file.write("sep=,\n")
    second_file.write("sep=,\n")

    nc = csv.writer(first_file)
    nc.writerow(header)
    nc.writerows(no_cache)

    c = csv.writer(second_file)
    c.writerow(header)
    c.writerows(cache)


