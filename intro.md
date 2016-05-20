Validation and verification are one of the essential parts of the software
development, as software bugs in a released product may become costly and
degrade the overall rating of the vendor, or even cause harm to the users.
Therefore, a lot of effort is usually put into this part of the development
process even though it is one of the most time-consuming and most expensive
part.

Testing is a widely adopted method in the industry, as it is quite simple and
does not require any complex tools. Usually only a simple testing framework and
an (automated) runtime environment is used. Even though this method is not sound
(it cannot prove the absence of a bug), it performs quite well in practice
during bug-finding in sequential code.

As multi-core CPUs are quite common today, multi-threaded software is required
to fully utilise them. Even mobile devices, such as cellphones, feature
multi-core CPUs and thus multi-threaded software is increasingly commonly
produced today. This kind of software is hard to test due to the presence of
non-determinism in thread scheduling. Two runs of the same program with the same
input can lead to a different threads interleaving. This can cause distinct
program behaviour for each run -- so-called race conditions. Multi-threaded
program tests are also affected by the scheduler's non-determinism, so it is
possible to obtain two different test results for two test runs. These bugs are
hard to find, as they can occur only in a single thread interleaving, which can
be scheduled only in very specific circumstances. Observation of the program
(e.g. run  when under a debugger or run in a different environment) can also
affect the scheduling and the bug might not occur.

A lot of effort has been put into the development of formal methods during the
last few decades. These methods could replace testing and would help to find
more bugs. There are methods like symbolic execution, bounded model checking and
others, which are in general unsound; however, they can help with discovery of
the hard-to-find bugs (e.g. integer overflow related bugs, memory safety etc.).
On the other hand, there are methods like deductive verification, model-checking
and others, which are sound, and, besides bug-finding, they can actually prove
absence of a bug. Many of these methods also support multi-threaded programs, so
it is possible to deterministically find bugs in multi-threaded software. This
could be one of the motivations to replace testing by these methods in the
industry.

Despite the promising features of the formal methods, they are not widespread in
the industry and stay mainly within the academic interest. There are several
reasons for that. First of all, techniques like deductive verification are not
automatized and require qualified user interaction. On the other hand, the
automatized techniques do not scale well to real world programs. Either they
cannot take an unmodified code and process it (manual annotation is needed, all
language features are not supported), or the verification needs an enormous
amount of computing resources for real-world code. Many tools fail to verify
real-world code due to substantial input data domain or complexity in control
flow.

One of the tools that aim for verification of real-world parallel C/C++ code is
\symdivine. This tool is a control-explicit data-symbolic model checker. Unlike
explicit-state model checkers, it can handle non-deterministic input well. It
allows user to take an unmodified C/C++ code with notation of input values and
verify it for reachability or \ltl properties. To alleviate state-space
explosion caused by input values, a so-called set-based reduction is incorporated
in this tool. The reduction is based on symbolic data representation, which
heavily uses quantified bit-vector \smt queries to an \smt solver.

In this thesis we propose and implement new optimizations for \smt machinery in
\symdivine in order to speed-up the verification task and thus help \symdivine
to scale better. Our optimizations are based on caching of \smt queries.

The thesis is organised as follows: first, we a make an short overview of
related topics in \autoref{chap:preliminaries}. Then we provide a detailed
description of \symdivine's internals that are essential for our thesis in
\autoref{chap:symdivine}. In \autoref{chap:caching} we make an overview of the
existing \smt caching solutions and propose a new one. The results of the
experimental evaluation of our optimization are presented in
\autoref{chap:results}. \autoref{chap:conclusion} summarizes our contribution
and discusses future work.
