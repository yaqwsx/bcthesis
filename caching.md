In this chapter we present our motivation for proposing and implementing \smt
several queries caching techniques for \smt data store in \symdivine. Then we
propose and in detail describe two approaches that we find interesting -- a
naive one, that lead to another optimization in \symdivine, and dependency-based
one, that brought noticeable speed up. In the following \autoref{chap:results},
we present experimental evaluation of our implementation of these techniques.

# Motivation

Scalability is an important factor of verification tool, that aims for
verification of real-world sized code. During various experiments with
\symdivine, we noticed that most of the verification time is spent on Z3 \smt
solver calls. We analysed \symdivine using time measurement and Callgrind tool
todo citace on verification task from SC-COMP concurrency set. In average,
roughly 70\ % of the time is spent on quantified \smt solvers calls and 10 % of
the time is spend on quantifier free queries.

As \symdivine focuses on multi-threaded programs, we suspect similar queries for
state equality and emptiness due to diamond-shapes in multi-state space. The
same or similar diamond-shapes can appear multiple times in the multi-state
space due to branching and thread interleavings. When queries during diamond-
shape exploration cannot be optimized-out by simple syntactic equality, multiple
the same queries to an \smt solver are made. Also many variables in path
condition are assigned only once as \llvm is a static single assignment
languages. Thus each query to an \smt solver can share significant amount of the
same information with previous queries.

Z3 \smt solver incorporates various caching techniques todo citace z3 to speed
up queries, however we are not aware of a technique, that could help us in our
particular case -- multiple constantly growing quantified \smt queries. The
traditional techniques does not work, as the quantifier in the `equal` query
makes splitting it into cacheable part hard. Also from our experience, making a
query to the Z3 brings a non-trivial overhead even for easy queries and we would
like to avoid it. And as last, we think that knowledge of our setting (origin of
path condition, semantic of the queries) can help us to perform optimizations
that cannot be performed or can be hard to perform in the \smt solver layer.

# Naive approach

We began our experiments with a naive approach -- caching of whole query for
multi-state equality. This naive approach can be seen as an extension of
syntactic equality optimization, that we described in
\autoref{subsec:symdivine:smt:impl}. Syntactic equality can eliminate a query to
an \smt solver in case of diamond shapes, that result in syntactically same path
condition. If this diamond-shape results in a syntactically different path
condition, \smt solver has to be called. If such a diamond appears in multi-
state space again, the same query is performed. If naive caching is present, the
second query to an \smt solver can be eliminated.

We have implemented this naive approach in \symdivine version from todo citace
Vilík. The naive caching is implemented using a hash-map from an \smt query to a
result of such query. In original implementation, `empty` query was directly
constructed in \smt solver native format. We have taken an advantage in form of
fixed query format, as wanted to kept the caching process independent of the
\smt solver and also minimize memory footprint. Only the essential parts to
uniquely identify a query are kept in the table -- list of variables pairs to
compare and path condition clauses. No other unnecessary parts of the syntactic
tree are kept. Just before the real \smt query is constructed, this footprint of
query is constructed and checked for presence in the cache. If so, cached result
is returned. Otherwise real query is constructed, executed and the result is
inserted into the cache.

We have evaluated naive approach using a subset of SV-COMP benchmarks (mainly
concurrency and bit-vector tasks) and a set of \ltl benchmarks by Byron Cook,
that have been used in evaluation of \symdivine in todo citace vojta. Naive
caching saved only about 6\ % in the reachability tasks, however up to 65\ % of
`empty` queries were cached in the \ltl benchmarks.

This result made us to revisit the implementation of the \ltl algorithm in
\symdivine. \symdivine uses nested DFS with iterative deepening, as bugs in
software are usually shallow and occur e.g. during first few iterations of a
cycle in a program. If \symdivine finds a cycle in a verified program, that
needs to be unrolled, classical DFS would first fully unrolled the cycle and
then searched the other parts of the multi-state space. Iterative deepening can
prevent this behaviour trading it off with verification time. The inspiration
for the implementation was taken from \divine, that also feature iterative
deepening DFS. \divine does not keep the state space graph and during every
iteration with increased depth it regenerates the state-space from scratch.
However generation of multi-state space is computationally more demanding
compared to generation of explicit-state space and the overhead caused be re-
generation of the multi-state space is not negligible as queries to an \smt
solver are involved. The re-generation of the multi-state space caused enormous
hit-rate and thus brought a significant speed-up.

As the original \ltl algorithm did not feature user-friendly way to pass an \ltl
property, we decided to implement new version that would keep the whole multi-
state space including the transition between states and brought the user-
friendliness. Keeping the transitions between the states caused a slightly
bigger speed up than naive caching in the original version. Also the hit-rate of
naive cache was reduced to similar levels as in case of reachability
verification tasks. Memory overhead of this solution is negligible taking in
account a size of an average multi-state.

# Dependency-based caching