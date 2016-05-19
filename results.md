In this chapter we present an experimental evaluation of our dependency-based
caching and we discuss strengths and weaknesses of our approaches. We have
evaluated both algorithms (reachability and \ltl) from the current version of
\symdivine with dependency-based caching.

# Benchmark Set and Environment

To evaluate reachability, we have taken a subset of C benchmarks from SV-COMP
\cite{SVCOMP} benchmark suite. Benchmarks from  the following subdirectories
were taken: bitvector, eca, locks, loops, recursive, ssh-simplified, systemc,
pthread, pthread-atomic, pthread-ext, pthread-lit and pthread-wmm. To evaluate
\ltl algorithm, we have used \ltl benchmarks, which have been used in
\cite{BHB14} for benchmarking of the first \ltl implementation in \symdivine.

Our test machine features Intel Core i5-4690 CPU (3.50\ GHz) with 16\ GB of RAM
and runs Arch Linux distribution with 4.4.8-1-lts Linux kernel. \symdivine was
built in the release configuration using \clang 3.4 and Z3 \smt solver version
4.4.1-1.

Three test files were produced from a single input benchmark file by compiling
it into \llvm bit-code with three different levels of optimizations -- `O0`,
`Os` and `O2`. Note that each \ltl benchmark is shipped with its specification
in the form of \ltl formula. We have tested each \ltl benchmark for its
specification and negation of the specification.

First of all, we ran \symdivine with different configurations (solver time-out,
simplification strategies, etc.) for both \smt data store and partial \smt data
store to find the optimal configuration for our set of benchmarks. \smt data
store performs best with the default setting (no command line flags -- advanced
simplifications of the path condition and syntactic equality optimizations are
enabled). Partial \smt data store performs best with the same setting, however,
simplifications of path conditions have to be disabled, as changing the the path
condition using simplifications leads to a zero cache hit-rate.

Using the optimal settings mentioned above, we ran \symdivine with partial \smt
store and caching enabled on the benchmark set with a time-out of 4 minutes for
each task. Then, we ran the same set of benchmarks without caching using the
original implementation of \smt store and time-out increased to 15 minutes. The
time-out was increased in order to see improvements caused by caching, as many
benchmarks without caching time-outed and no relevant data cannot be obtained.
Simple benchmarks with no equal queries were excluded from the final results as
they are not relevant to caching.

We also verified correctness of the implementation of partial \smt store. We
implemented a so-called *validity test* in partial \smt store. This validity
test keeps 2 multi-states -- one represented by \smt store and the other one by
partial \smt store. All multi-state manipulations are performed simultaneously
on both stores. When an empty or an equal operation is performed, results of
partial \smt store are tested against \smt store. The results have to match. We
ran all benchmarks mentioned above using this test and not a single mismatch
occurred.

# Evaluation

We examined the results of each category independently, to see the effects of
caching on different types of input programs. For summary results of our
measurements\footnote{Full measurements can be found in the electronic archive
submitted with this thesis}, follow \autoref{tab:summary}. We looked at the
verification time and number of queries to an \smt solver. A short evaluation of
results for each category is provided below:

\paragraph{bitvector} There are many simple benchmarks in this set that contain
only the necessary constructions to produce a bug in bit-vector manipulation.
\autoref{fig:bitvector_set} shows that caching overhead is compensated with its
positive effect on small benchmarks and therefore verification time differs only
by less than one percent. On the other hand, there are benchmarks like `gcd*`,
where caching saved over $50~\%$ of verification time, as there is a sub-formula
in the path condition that causes troubles to the Z3 solver. Using caching,
this sub-formula is used only once as the result is cached. In summary, almost
half of the verification time can be saved using caching.

\paragraph{eca} This is the single category that exploited weaknesses of our
caching approach as can be seen in \autoref{fig:eca_set}. Benchmarks from this
set are generated pieces of code with an enormous number of variables and
non-trivial dependencies and therefore the overhead of caching is noticeable.
Even compilation of these benchmarks takes an unexpected amount of time (usually
a few minutes).

\paragraph{locks} Almost all benchmarks in this category are simple enough to be
directly solved by optimization passes in \clang -- optimizations in the
compiler are able to simplify the benchmarks up to a single branching. Therefore
\symdivine produces only 3 multi-states, and thus, the results, which can be
seen in \autoref{fig:locks_set}, are not significant.

\paragraph{loops} Many benchmarks in this category suffer from the same issue as
benchmarks in locks category -- many of them can be solved by the compiler
itself. However, verification time of complicated benchmarks can be reduced in
summary by almost $30~\%$, see \autoref{fig:loops_set}. This observation is in
line with our expectations (equality of intermediate results in program run is
evaluated only once when caching is used).

\paragraph{recursive} There are no effects of caching in programs with
recursion, as can be seen in \autoref{fig:recursive_set}. This is due to the
fact that multi-states produced in recursion cannot be merged, as their explicit
control-flow location differs.

\paragraph{ssh-simplified and systemc} Benchmarks from this category are quite
large and feature a similar structure to loops benchmarks, therefore caching
provides a good performance and can save in average about half of the
verification time (in some benchmarks even $75~\%$ of verification time can be
saved). These results can be seen in \autoref{fig:ssh_set} and
\autoref{fig:systemc_set}. Note the significant decrease in number of
solver queries.

\paragraph{concurrency} We expected the most significant effect of caching in
concurrency benchmarks due to the presence of diamond-shapes in multi-state
space. Even though almost half of the verification time is saved using caching,
there is systemc category, where caching performed slightly better. The reason
for such a behaviour is as follows: many equal queries on diamond-shapes can be
optimized out by the syntactic equality optimization. This optimization does not
apply to other categories, as the other benchmarks are sequential -- compare
number of equal queries and solver calls in \autoref{tab:summary}). Therefore
there are not as many \smt queries, which can be cached. With disabled syntactic
equality optimization, caching saves in summary $95~\%$ of verification time and
issue only $2~\%$ of solver queries (1769313 queries without caching compared to
45917 queries with caching), which meets our original expectations. Also,
benchmarks in this set do not contain complicated arithmetic, so the queries
to an \smt solvers are quite simple and the benefit of caching is not
significant as in other categories.

\paragraph{\ltl} There are two kinds of benchmarks in this set; ones that are
very simple and contain almost no arithmetic, and the others, that contain a
loop, which has to be fully unrolled and therefore they cannot be verified by
\symdivine in a reasonable amount of time. An interesting phenomena appeared in
these simple benchmarks -- all equal queries were decided using only syntactic
equality. When a product of a multi-state space and an automaton is generated,
transition guards are pushed to the multi-states and diamond shapes are
produced. However, pushing transition guards in different order produces a
syntactically different path condition and therefore no syntactical equality was
detected. In contrast, pushing transition guards to sub-states in different
order produces syntactically equal path conditions (as the conjuncts are not
interleaved). Even though no queries were made, no speed-up occurred, as can be
seen in \autoref{fig:ltl}.

\paragraph{Overall} We observed following behaviour from all our test runs: in
summary, caching reduces verification time by $44.8~\%$. Caching applies mainly
to the large benchmarks, where it can save up to $75~\%$ of verification time.
If caching does not bring a speed-up, usually only a negligible slow-down in units
of percent occurs (except benchmarks from the artificial eca set). The overall
positive results are summarized in \autoref{fig:overall_set}. We can conclude
that the speed-up produced by dependency-based caching is caused by several
factors:

* Smaller and simpler queries to an \smt solver are issued.

* Number of queries is reduced by caching.

* Number of queries is further reduced by the fact that the syntactic equality
  optimization can work even in sequential benchmarks when multi-states are
  split into sub-states.

\noindent In our test case, dependency-based caching issued 5 times less queries
compared to \symdivine with no caching.

\input{summary_table.tex}

\begin{figure}
    \input{bitvector_chart.tex}
    \caption{Effect of caching on bitvector benchmark set. Diagram depicts how
    many benchmarks could be solved within given time-out.}
    \label{fig:bitvector_set}
\end{figure}

\begin{figure}
    \input{eca_chart.tex}
    \caption{Effect of caching on eca benchmark set. Diagram depicts how
    many benchmarks could be solved within given time-out.}
    \label{fig:eca_set}
\end{figure}

\begin{figure}
    \input{locks_chart.tex}
    \caption{Effect of caching on locks benchmark set. Diagram depicts how
    many benchmarks could be solved within given time-out.}
    \label{fig:locks_set}
\end{figure}

\begin{figure}
    \input{loops_chart.tex}
    \caption{Effect of caching on loops benchmark set. Diagram depicts how
    many benchmarks could be solved within given time-out.}
    \label{fig:loops_set}
\end{figure}

\begin{figure}
    \input{recursive_chart.tex}
    \caption{Effect of caching on recursive benchmark set. Diagram depicts how
    many benchmarks could be solved within given time-out.}
    \label{fig:recursive_set}
\end{figure}

\begin{figure}
    \input{ssh_chart.tex}
    \caption{Effect of caching on ssh-simplified benchmark set. Diagram depicts how
    many benchmarks could be solved within given time-out.}
    \label{fig:ssh_set}
\end{figure}

\begin{figure}
    \input{systemc_chart.tex}
    \caption{Effect of caching on systemc benchmark set. Diagram depicts how
    many benchmarks could be solved within given time-out.}
    \label{fig:systemc_set}
\end{figure}

\begin{figure}
    \input{concur_chart.tex}
    \caption{Effect of caching on concurrency benchmark set. Diagram depicts how
    many benchmarks could be solved within given time-out.}
    \label{fig:concurrency_set}
\end{figure}

\begin{figure}
    \input{ltl_chart.tex}
    \caption{Effect of caching on \ltl benchmark set. Diagram depicts how
    many benchmarks could be solved within given time-out.}
    \label{fig:ltl_set}
\end{figure}

\begin{figure}
    \input{summary_chart.tex}
    \caption{Overall summary of caching effect. Each point represents a single
    benchmark. Benchmarks under the blue line are the ones, which can be
    verified faster using caching.}
    \label{fig:overall_set}
\end{figure}