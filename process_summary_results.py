#! /usr/bin/env python

import sys, csv, os
from functools import partial
from process_results_common import *

no_cache = []
cache = []

table = "\\begin{table}\n"
table += "\t\\caption{Summary results showing effects of caching for each benchmark category.}\\label{tab:summary}\n"
table += "\t\\begin{tabular}{l@{\hskip 0.1cm}rrrrrrrR{1.7cm}}\n"
table += "\t\t\\mcrot{1}{l}{60}{\\pbox{20cm}{Category  \\\\ name}} & \\mcrot{1}{l}{60}{\\pbox{20cm}{Time without \\\\ caching [s]}} & \\mcrot{1}{l}{60}{\\pbox{20cm}{Time with \\\\ caching [s]}} & \\mcrot{1}{l}{60}{\\pbox{20cm}{Percentage \\\\ difference}} & \\mcrot{1}{l}{60}{Equal queries} & \\mcrot{1}{l}{60}{\\pbox{20cm}{Solver queries \\\\ without cache}} & \\mcrot{1}{l}{60}{\\pbox{20cm}{Solver queries \\\\ with cache}} \\\\ \\toprule\n"


tt_nc = 0
tt_c  = 0
teq   = 0
ts_nc = 0
ts_c  = 0

for x in sys.argv[2:]:
    nc_f = os.path.join(x, "no_cache_no_flags.csv")
    c_f  = os.path.join(x, "cache_partial_store_dontsimplify.csv")
    with open(nc_f, "rb") as first_file, open(c_f, "rb") as second_file:
        header, nc = prepare_csv(first_file)
        _, c = prepare_csv(second_file)
        get = partial(get_item, get_mapping(header))
        set = partial(set_item, get_mapping(header))
        init(get, set)

        nc, c = prepare_data(nc, c)

        t_nc = 0
        t_c  = 0
        eq   = 0
        s_nc = 0
        s_c  = 0
        for nc_r, c_r in zip(nc, c):
            t_nc += get(nc_r, "time")
            t_c  += get(c_r, "time")
            eq   += get(c_r, "SMT calls Subseteq()")
            s_nc += get(nc_r, "SMT calls Subseteq()") - get(nc_r, "SMT subseteq on syntax. equal")
            s_c  += get(c_r, "Miss count")

        tt_nc += t_nc
        tt_c  += t_c
        teq   += eq
        ts_nc += s_nc
        ts_c  += s_c

        row = [os.path.basename(os.path.normpath(x)),
                   tex_math("\\SI{{{:.1f}}}{{}}".format(t_nc)),
                   tex_math("\\SI{{{:.1f}}}{{}}".format(t_c)),
                   tex_math("\\SI{{{:.1f}}}{{\percent}}".format((t_c / t_nc - 1) * 100)),
                   tex_math("{0}".format(eq)),
                   tex_math("{0}".format(s_nc)),
                   tex_math("{0}".format(s_c))]

        table += "\t\t" + " & ".join(row) + " \\\\ \\midrule\n"

        no_cache += nc
        cache += c

with open(sys.argv[1], "wb") as f:
    for nc, c in zip(no_cache, cache):
        f.write("{0}\t{1}\n".format(get(nc, "time"), get(c, "time")))

tt_nc += t_nc
tt_c  += t_c
teq   += eq
ts_nc += s_nc
ts_c  += ts_c

li = table.rsplit("\\midrule", 1)
table = "\\bottomrule".join(li)

row = ["\\textbf{summary}",
           tex_math("\\SI{{{:.1f}}}{{}}".format(tt_nc)),
           tex_math("\\SI{{{:.1f}}}{{}}".format(tt_c)),
           tex_math("\\SI{{{:.1f}}}{{\percent}}".format((tt_c / tt_nc - 1) * 100)),
           tex_math("{0}".format(teq)),
           tex_math("{0}".format(ts_nc)),
           tex_math("{0}".format(ts_c))]

table += "\t\t" + " & ".join(row) + " \\\\ \\bottomrule \n"

table += "\t\\end{tabular}\n"
table += "\\end{table}\n"

with open("summary_table.tex", "w") as f:
    f.write(table)