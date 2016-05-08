Trading off time for space is a basic approach to improving the time efficiency
and scalability of software tools. Storing results of intermediate results can
be significantly less time consuming than re-computation and thus bring a speed
up of a tool.

In this chapter we present our motivation for proposing and implementing several
\smt queries caching techniques for \smt data store in \symdivine. We provide a
quick overview over existing caching solutions and their suitability for our
case. Then we propose and in detail describe two approaches that we find
interesting -- a naive one, that lead to another optimization in \symdivine, and
dependency-based one, that brought up a noticeable speed up. In the following
\autoref{chap:results}, we present experimental evaluation of our implementation
of these techniques.

# Motivation

Scalability is an important factor of verification tool, that aims for
verification of real-world sized code. During various experiments with
\symdivine, we noticed that most of the verification time is spent on Z3 \smt
solver calls. We analysed \symdivine using time measurements and Callgrind tool
todo citace on verification task from SC-COMP concurrency set. \smt data store
in \symdivine performs two kind of \smt queries -- a quantified query for
decision of multi-state equality and a quantifier-free query for emptiness check
(both described in \autoref{sec:symdivine:smtstore}). In average, roughly 70\ %
of the time is spent on quantified \smt solvers calls and 10 % of the time is
spend on quantifier free queries.

There are two reasons why we think caching of queries might be effective. First,
\symdivine constructs a path condition in a similar manner as symbolic execution.
Thus a constantly growing formula sharing a common prefix is constructed. This
growth is also supported by the fact, that \llvm is a single static assignment
language and thus uses enormous number of registers. The multi-state emptiness
check is performed in the same manner as in symbolic execution.

Second, \symdivine focuses on multi-threaded programs and various thread
interleavings can cause so-called diamond-shapes in the multi-state space. This
means that two paths in a multi-state space join to the same state and an
equality check has to be performed. See illustration todo ref of this phenomena.
Also multiple the same or similar diamond-shapes can occur multiple time in
different parts of a multi-state space. Syntactic equality optimization works in
some cases. However there might be a diamond-shape that can be resolved only
using the \smt query. When such a diamond-shape appears multiple times, the same
query to an \smt solver needs to be issued.

Caching of both, empty and equal, queries can bring a speed-up. Z3 \smt solver
incorporates various caching techniques todo citace z3 to speed up queries, that
might work for the emptiness check (a batch of quantifier-free queries sharing
common prefix). However we are not aware of a technique, that could help us in
case of equality check (a batch of quantified \smt queries that include a
sub-formula with growing common prefix). Also we see bigger potential in the
equal query, as it is computationally more demanding. The traditional techniques
does not work, as the quantifier in the query makes slicing it into cacheable
parts computationally hard or even in some cases impossible. Also from our
experience, making a query to the Z3 brings a non-trivial overhead even for easy
queries and thus we would like to avoid it (the same phenomena was observed in
todo citace vojta). We think bringing a knowledge of our setting (fixed format
of the equal query and its semantics or path condition origin) can help us to
face the issue and design an effective caching technique.

# Classical Approaches In Other Tools

There are no resources we are aware of, that in detail describe all caching
optimization implemented in Z3. Only a brief overview can be found in ToDo
citace Z3. However from this overview and our shallow knowledge of Z3 source
code, we assume that in principle, the caching optimizations work in a similar
manner as optimizations that can be found in KLEE todo, PEX todo (both are tools
for symbolic execution) or in GREEN todo (framework for caching \smt queries
during symbolic execution). Z3 also features a cache for the built in SAT
solver, on top of which the \smt solver is built.

In principle there can be found two main approaches to caching -- constraints
caching and unsatisfiable cores caching. Both of these approaches are suited for
purposes of symbolic execution and are designed to handle a batch of
quantifier-free \smt formulae with common prefixes.

Constraints caching takes advantage of the way a path condition in symbolic
execution is build. As the symbolic execution collect new constraints, new
conjuncts are added to the formula. Thus the queries follow form $\varphi \wedge
\psi$, where $\varphi$ denotes the known part of the path condition (that was
already issued as a query) and $\psi$ denotes part of the formula with new
conjuncts. If $\varphi$ is not satisfiable according to a cached result, the
whole query cannot be satisfiable. Otherwise $\varphi$ and $\psi$ are
syntactically analysed and only conjuncts from $\varphi$ that share a variable
with $\psi$ are taken. Satisfiability of this smaller formula is then decided.
To effectively select only the necessary conjuncts of $\varphi$, GREEN todo
citace builds a tree structure over existing parts of the path condition. Also
before deciding satisfiability, parts of the formulae are canonized to increase
the chance of a cache hit.

Unsatisfiable cores caching can be seen as extension of the previous techniques.
When an unsatisfiable query is issued, the unsatisfiable core is computed and
transformed into a pattern. When a new query is processed, it is first checked
for a presence of unsatisfiable patterns that have been seen so far.

These approaches work well for quantifier-free queries that are produced during
symbolic execution. However from our experiences and experiments performed with
Z3, we assume that these caching optimizations are not applied to quantified
queries at all or does not have any noticeable effect. We are also not aware of
any work, that would specialize on caching of quantified formulae.

# Naive Approach

We began our experiments with a naive approach -- caching of whole query for
multi-state equality. This naive approach can be seen as an extension of
syntactic equality optimization, that we described in
\autoref{subsec:symdivine:smt:impl}. Syntactic equality can eliminate a query to
an \smt solver in case of diamond shapes, that result in the syntactically same
path conditions. If this diamond-shape results in a syntactically different path
conditions, \smt solver has to be called. If such a diamond appears in multi-
state space again, the same query is performed. If naive caching is present, the
second query to an \smt solver can be eliminated.

We have implemented this naive approach in \symdivine version from todo citace
Vilík. The naive caching is implemented using a hash-map from an \smt query to a
result of such query. In original implementation, `empty` query was directly
constructed in \smt solver native format. We have taken an advantage in form of
fixed query format, as we wanted to kept the caching process independent of an
\smt solver (queries are not constructed using formulae representation of
\symdivine, but directly in the target \smt solver format) and also minimize
memory footprint. Only the essential parts to uniquely identify a query are kept
in the table -- list of variables pairs to compare and path condition clauses.
No other unnecessary parts of the syntactic tree are kept. Just before the real
\smt query is constructed, this footprint of query is constructed and checked
for presence in the cache. If so, cached result is returned. Otherwise real
query is constructed, executed and the result is inserted into the cache.

We have evaluated naive approach using a subset of SV-COMP benchmarks (mainly
concurrency and bit-vector tasks) and a set of \ltl benchmarks by Byron Cook,
that have been used in evaluation of \symdivine in todo citace vojta. Naive
caching saved only about 6\ %  in the reachability tasks, however up to 65\ % of
the queries were cached in the \ltl benchmarks.

This result made us to revisit the implementation of the \ltl algorithm in
\symdivine. \symdivine uses nested DFS with iterative deepening, as bugs in
software are usually shallow and occur e.g. during first few iterations of a
cycle in a program. If \symdivine finds a cycle in a verified program, that
needs to be unrolled, classical DFS approach would first fully unrolled the
cycle and then searched the other parts of the multi-state space. Iterative
deepening can prevent this behaviour and thus speed-up verification of erroneous
programs. However verification of programs with no bug takes longer. The
inspiration for the implementation was taken from \divine, that also feature
iterative deepening DFS. \divine does not keep the state space graph and during
every iteration with increased depth it regenerates the state-space from
scratch. However generation of multi-state space is computationally more
demanding compared to generation of explicit-state space and the overhead caused
be re- generation of the multi-state space is not negligible as queries to an
\smt solver are involved. The re-generation of the multi-state space caused
enormous hit-rate and thus brought a significant speed-up. Note that similar
effect was not observed on reachability, as it uses BFS based approach.

As the original \ltl algorithm did not feature user-friendly way to pass an \ltl
property, we decided to implement new version that would keep the whole
multi-state space including the transitions between states and brought the
user-friendliness. Keeping the transitions between the states caused a slightly
bigger speed up than naive caching in the original version. Also the hit-rate of
naive cache was reduced to similar levels as in case of reachability
verification tasks. Memory overhead of this solution is negligible taking in
account the size of an average multi-state.

# Dependency-based caching

In this section we introduce our approach for caching equal queries in \smt data
store in \symdivine. Our approach shares similar ideas as constraints caching,
however it uses an additional information about the structure of the query, that
an advantage can be taken of.

Let us briefly remind the structure of equal query in \symdivine. The equal
query for states $A$ and $B$ is split into two separate tasks -- test if $A$ is
not a subset of $B$ or if $B$ is not a subset of $A$. Each notsubseteq test
performs following query to an \smt solver:
\begin{equation}
    \exists b_0,\dots,b_n\ldotp \psi \wedge \forall a_0,\dots,a_n\ldotp \varphi
    \implies
        \left(
            \bigvee \left(a_i \neq b_i\right)
        \right) \nonumber
\end{equation}
where $\varphi$ is a path condition of $A$, $\psi$ is a path condition of $B$
and $a_0,\dots,a_n$; $b_0,\dots,b_n$, denotes variables from $A$, $B$
respectively.

The unsatisfaible cores caching has no effect on our query, as \symdivine
ensures that $\varphi$ and $\psi$ are both satisfiable independently (empty
multi-states are never checked for equality). To apply a constraints caching,
detecting the new parts of formula (compared to already seen formulas) is
needed. Here we face the problem that we cannot easily split the formula in the
similar manner into conjuncts due to the presence of universal quantifier, that
captures part of the formula and also the implication in the quantified part.

These issues could be solved by detecting the formula growth on $\psi$,
$\varphi$ and the sets of variables. Then a dependencies across these part could
be computed and a new, smaller query could be produced. However we see this as
complicated and rather computationally challenging. Instead, we take an another
point of view by using the semantics of the query and the possibility to change
the equality procedure to suite the needs of caching.

In our approach we represent multi-state data as a multiple independent sets of
valuations instead of a single one. We define two sets of valuations as
independent, when every change on the one of them leaves the second one
unchanged. In our case of valuations representation using path conditions, each
set is defined by a single path condition. We can simplify the requirements for
independence to following. Two path conditions are independent if the share no
common variable. This requirement is stronger, however from the practical point
of view, they are the same. This set-up can be also seen as splitting a
program's multi-state into several smaller mutually independent states. We will
refer these as a sub-states. See \autoref{fig:multimultistate} for illustration
of dividing a multi-state to a set of sub-states.

\begin{figure}[!ht]
\begin{center}
\resizebox{0.8\textwidth}{!}{
    \begin{tikzpicture}[ ->, >=stealth', shorten >=1pt, auto, node distance=1.5cm
                       , semithick
                       , scale=0.7
                       , font=\sffamily
                       , stateprog/.style={ rectangle, draw=black, very thick,
                         minimum height=2em, minimum width = 10em, inner
                         sep=6pt, text centered, node distance = 2em, align = left,  rounded corners }
                       ]

        \node[stateprog, label=Original multi-state] (p1)
            {Program counter: x \\
             Path condition clauses: \\
             $a < 42$ \\
             $a > 0 $ \\
             $b = a + 4$ \\
             $c > 42$
             };

        \node[text centered, align = left, above right = -3.1em and 6em of p1] (pc)
            {Program counter: x  \\
             Substates: };
        \node[stateprog, below = 0.5em of pc] (p2)
            {$a < 42$ \\
             $a > 0 $ \\
             $b = a + 4$};
        \node[stateprog, below = 0.5em of p2] (p3)
            {$c > 42$};

        \node[stateprog, fit = (pc) (p2) (p3), label=New multi-state] {};
    \end{tikzpicture}
    }
    \caption{Illustration of new representation of multi-state. Instead of
    keeping one path condition, multiple mutually independent path conditions
    are kept -- so-called sub-states. This set-up allows more effective
    implementation of equal query when using caching.}
    \label{fig:multimultistate}
\end{center}
\end{figure}

This set-up reflects commonly seen situation in multi-states of a verified
program. During nested function calls, many registers of the programs are left
unmodified and they have no effect on current multi-state transformation during
interpretation of an \llvm bit-code. Thus, we can isolate these registers to
(even multiple) independent states, that are not modified during current
transformation. Another situation can occur during a verification of
multi-threaded program. It is possible to have two threads, that does not
communicate (share no memory). Using sub-states, each thread can operate in its
own sub-state and advance of one thread does not modify sub-state of the other
one.

A sub-state can be in context of a single multi-state uniquely identified by set
of variables it contains -- we call this set a *sub-state label*. We say, that
*two sub-states from different multi-states match* if and only if they have the
same label. We say *two multi-states $A$ and $B$ match* if and only if there is
a matching sub-state in $B$ for every sub-state in $A$. Multi-state can be
divided into sub-states in many ways. To decide whether two multi-states are
equal, these two multi-states has to match. Provided this set-up, we can say
states $A$ and $B$ are equal if and only if every sub-state from $A$ is equal to
its matching state in $B$. As all sub-states are independent, proof of this
statement is trivial.

To be able to decide equality of any two multi-states, we define operations
*split a sub-state* and *merge two sub-states* that allows transformation of
every two states into matching form. Merging of sub-states is straightforward,
we create conjunction of their path conditions a make a set union of their
labels. Splitting a sub-state into two sub-states is possible if clauses of the
original path conditions can be split into two sets of clauses such that they
are independent (share no common variable). We call a sub-state *trivial* if it
cannot be split any more. Note that every two multi-states (with the same
control part) can be transformed into a matching form, as we can in the
worst-case scenario merge all sub-states to a single one and thus, produce a
sub-state equivalent to a multi-state without sub-states.

Our motivation for introduction of sub-states is straightforward -- provided the
above-mentioned equality procedure and keeping as many trivial sub-states as
possible, we produce smaller and more simple queries to an \smt solver. We also
expect a high cache hit-rate, as in real-world programs, only very few variables
has effect on current transformation of multi-state.

Compared to performing similar operations directly on the queries produced by
\smt store, we can compute the the data dependencies on the fly with no
significant overhead during path condition generation. Thus, we avoid the
overhead of building a large query for an \smt solver followed by its analysis
and slicing. Instead, we can directly produce small queries that can be cached
and also take benefits of other optimizations in \symdivine, that can work on
top of these small queries. We call this approach *dependency-based caching*.

# Implementation of Partial Store

In this section we provide in detail description of our dependency-based caching
implementation in \symdivine and make an overview of small differences to the
theoretical description provided in previous section.

We have implemented this caching technique as a new data store -- *partial
store*. As a non-trivial part of the data store interface is implemented in the
same manner as \smt store (e.g. all `implement_{op}` functions), we abstracted
them to a new base class.  Both \smt and partial store are derived from this
class. Thus we needed to provide only segment related function, `deref`, `load`,
`store`, `prune` and `implement_input` functions.

We have implemented a data structure called *dependency group*. This structure
represents a sub-state from previous section. Dependency group keeps its label,
list of path condition and list a definitions as it implements the same
optimization as \smt data store. It provides interface for performing dependency
groups merging and splitting. Also several support function of purely technical
characters are implemented.

Partial store keeps instead of path condition and definitions a set of
dependency groups and mapping from variables to these dependency groups. When a
new variable is created, it is not dependant on any other and thus a new
dependency group is created for every newly created variable. When a segment
with all variables is destroyed, substitution of variable definitions is perform
just like in \smt store. As the dependency groups are independent, substitution
occurs only in a context of a single group. If the group label is after deletion
empty, the group is destroyed.

If a `store` or `prune` operation is issued, variables from an expression or a
constrain are collected, their dependency groups are located and merged.
Definition or a path condition is then inserted into the group. This
implementation keeps the invariant that dependency groups are always
independent. When performing `store` or `prune` operation would violate the
invariant, affected groups are merged.

The other operations are implemented in the same manner as operations in \smt
store. The only difference is, that corresponding dependency group has to be
located first.

Test for state emptiness is performed for each resource group independently and
each group caches result of this check. If path condition is modified, result in
cache is discarded and the check is repeated. This is an small optimization,
that was not introduced in the theoretical description. And produces small
speed-up.

To perform equality check, multi-states needs to be first converted to matching
form. Not only dependency groups can differ, also a variable naming can be
different as the mapping between call stack and segments is not canonical. To
effectively compute which group needs to be merged, we first obtain a list of
variables pairs to compare just like \smt store does. Then we iterate over this
list and using union-find, according groups labels we build sets of groups that
need to be merged. Then a standard equality check from \smt store is performed
for each merged group. To cache these calls, the same approach as the naive one
is used.
