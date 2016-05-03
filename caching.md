In this chapter we present our motivation for proposing and implementing \smt
queries caching techniques for \smt data store in \symdivine. Then we propose
and in detail describe two approaches -- a naive one and dependency-based one.
In the following chapter todo citace, we present experimental evaluation of our
implementation of these techniques.

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

# Dependency-based caching