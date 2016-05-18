#! /usr/bin/env python

import sys, csv
from functools import partial
from process_results_common import *

with open(sys.argv[1], "rb") as first_file, open(sys.argv[2], "rb") as second_file:
    header, no_cache = prepare_csv(first_file)
    _, cache = prepare_csv(second_file)
    get = partial(get_item, get_mapping(header))
    set = partial(set_item, get_mapping(header))
    init(get, set)

# print(header)
# print("\n")

no_cache, cache = prepare_data(no_cache, cache)

if not check_validity(cache, no_cache):
    print("Names does not match!")
    sys.exit(1)

## Generate CSV with results
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

## Write result
with open("_res.csv", "wb") as f:
    f.write("sep=,\n")
    cc = csv.writer(f)
    cc.writerow(res_header)
    cc.writerows(res)

## Write tex table with the results
with open("table.tex", "w") as f:
    f.write("\\begin{landscape}\n\t\\begin{longtable}{l@{\\hskip 0.5cm}rrrrrrrrR{1.5cm}}\n")

    # Header
    header = [tex_table_header("Benchmark name"),
              tex_table_header_r("Multi-states"),
              tex_table_header_r(tex_join_lines("Instructions", "executed")),
              tex_table_header_r(tex_join_lines("Time without", "caching [s]")),
              tex_table_header_r(tex_join_lines("Time with", "caching [s]")),
              tex_table_header_r(tex_join_lines("Time", "difference [s]")),
              tex_table_header_r(tex_join_lines("Percentage", "difference")),
              tex_table_header_r("Equal queries"),
              tex_table_header_r(tex_join_lines("Solver queries", "without cache")),
              tex_table_header_r(tex_join_lines("Solver queries", "with cache"))]

    f.write("\t\t\t\\caption{\\tablecaption}\\label{\\tablelabel}\\\\\n");
    f.write("\t\t\t" + " & ".join(header) + " \\\\\n")
    f.write("\t\t\t\\toprule\n")
    f.write("\t\t\t\\endfirsthead\n\n")

    f.write("\t\t\t\\caption*{\\textbf{Continued:}~\\tablecaptioncont}\\\\\n");
    f.write("\t\t\t" + " & ".join(header) + " \\\\\n")
    f.write("\t\t\t\\toprule\n")
    f.write("\t\t\t\\endhead\n\n")

    f.write("\t\t\t\\multicolumn{10}{c}{\\textit{Continue...}}\\\\\n")
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
        x[0] = x[0].replace(".ll_neg", "_neg.ll")
        x[0] = x[0].replace("succeed", "succ")
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
