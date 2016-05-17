#! /usr/bin/env python

import sys, csv, os
from functools import partial
from process_results_common import *

no_cache = []
cache = []

for x in sys.argv[2:]:
    nc_f = os.path.join(x, "no_cache_no_flags.csv")
    c_f  = os.path.join(x, "cache_partial_store_dontsimplify.csv")
    with open(nc_f, "rb") as first_file, open(c_f, "rb") as second_file:
        header, nc = prepare_csv(first_file)
        _, c = prepare_csv(second_file)
        get = partial(get_item, get_mapping(header))
        set = partial(set_item, get_mapping(header))
        init(get, set)
        no_cache += nc
        cache += c

no_cache, cache = prepare_data(no_cache, cache)

with open(sys.argv[1], "wb") as f:
    for nc, c in zip(no_cache, cache):
        f.write("{0}\t{1}\n".format(get(nc, "time"), get(c, "time")))