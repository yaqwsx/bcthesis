#! /usr/bin/env python

import sys, csv
from functools import partial

def init(g, s):
    global get
    global set
    get = g
    set = s

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

    no_cache, cache = filter_no_equal(no_cache, cache)

    # cache = timeout_to_val(cache, 240)
    # no_cache = timeout_to_val(no_cache, 240)

    return no_cache, cache

def tex_table_header(s):
    return s

def tex_table_header_r(s):
    return "\\mcrot{1}{l}{60}{" + tex_table_header(s) + "}"

def tex_join_lines(a, b):
    return "\\pbox{20cm}{" + a + " \\\\ " + b + "}"

def tex_math(s):
    return str(s)
    return "$" + str(s) + "$"