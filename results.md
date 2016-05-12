In this chapter we present experimental evaluation of our dependency-based
caching a we discuss strengths and weaknesses of our approaches.

# Reachability benchmarks

We have taken a subset of C benchmarks from SV-COMP \cite{SVCOMP} benchmark
suite. Benchmarks from following subdirectories were taken: bitvector, eca,
locks, loops, recursive, ssh-simplified, systemc, pthread, pthread-atomic,
pthread-ext, pthread-lit and pthread-wmm. We ran \symdivine without caching on a
machine with Intel Core i5-4690 CPU (3.50\ GHz) and 16\ GB of RAM. Each
benchmark was compiled with three different level of optimizations into \llvm
bit-code -- `-O0`, `-Os` and `-O2`. All benchmarks run with time-out 4 minutes.
We ran \symdivine with original \smt store and multiple different configurations
using \smt partial store, which implements dependency-based caching.

We also verified correctness of implementation of partial \smt store. We
implemented so-called *validity test* in partial \smt store. This validity test
keeps 2 multi-states -- one represented by \smt store and the other one by
partial \smt store. All multi-state manipulations are performed simultaneously
on both stores. When an empty or an equal operation is performed, results of
partial \smt store are tested against \smt store. The results has to match. We
ran all benchmarks mentioned above using this test and not a single mismatch
occurred.

# \ltl benchmarks

We have taken C LTL benchmarks that have been used in \cite{BHB14} for
benchmarking of first \ltl implementation in \symdivine. Then we followed
similar methodology as during benchmarking reachability. For every benchmark, 3
different \llvm bit-codes with different levels of optimizations were produced.
Then we ran \symdivine with timeout 4 minutes. We have tested validity of given
property for each benchmark and its negation. Comparison of results can be seen
Todo