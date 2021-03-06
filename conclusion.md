We showed that caching of queries to an \smt solver is a possible way of
speeding-up control-explicit data-symbolic model checkers. To do that, we
proposed *dependency-based* caching, a method for decomposition of quantified
\smt queries and follow-up memorization of its results, and performed evaluation
of our implementation in the \symdivine model checker.

Decomposition of queries in dependency-based caching takes inspiration from
classical caching algorithms for quantifier-free \smt queries used in symbolic
execution, and extends the core idea to quantified queries in control-explicit
data-symbolic model checking while taking advantage of the way it is constructed
in these tools. It works by computing data dependencies among variables and
splitting a single multi-state into multiple so-called sub-states according to
the dependencies. This allows to split a single large \smt query into multiple
smaller ones, whose satisfiability results can be memorized, and therefore
prevent issuing the same query again.

Dependency-based caching was implemented in \symdivine and evaluated using
SV-COMP benchmarks for reachability and several other benchmarks for \ltl model
checking. The evaluation shows that caching can save a large amount of
verification time for large benchmarks (in our experiments up to $75~\%$) and
therefore bring verification of real-world sized parallel programs closer to
reality. Our experiments show that, in summary, verification can be two times
faster using dependency-based caching.

While working on this thesis, we improved usability and performance of \ltl
model checking algorithm in \symdivine. We have also uncovered a bug in the
implementation, which made some runs of a verified program infeasible and
therefore \symdivine could provide false negative results in some cases.

# Future Work

In the future, we would like to make a more detailed examination of \smt queries
in \symdivine. We would like to experimentally evaluate if issuing queries as
small as possible leads to an optimal performance of an \smt solver or if we
could benefit from issuing large queries produced by merging several sub-states
together.

\symdivine currently supports only Z3 \smt solver. It would be interesting to
implement support for other solvers and compare the effect of caching. We would
also like to explore the possibilities of optimizations like purely syntactic
equality of state, as we have seen that these optimizations can be more
effective when issued on sub-states instead of multi-states.

Finally, there is a potential in canonization of control-flow location
representation, as we realised during the development of caching techniques. In
the current version of \symdivine, threads are identified by the order in which
they are created. This can lead to a production of two multi-states with
different thread naming and the same data valuation. However, due to the naming,
they are considered to be different. Canonization of control-flow location
representation would lead to merging such two states and therefore to the
reduction of the multi-state space.
