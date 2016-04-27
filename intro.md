Validation and verification are one of the essential parts of the software
development as software bugs in a released product may become costly and degrade 
overall rating of the vendor or even cause harm to the users. Thus there is
usually a lot of effort put into this part of the development process even it is
one of the most time consuming and the most expensive part of it.

Testing is widely adopted method in the industry as is quite simple and does not 
require any complex tools. Usually only a simple testing framework and an
(automated) runtime environment is used. Even though this method is not sound 
(it cannot prove absence of a bug), it performs quite well in practise during
bug-finding in sequential code.

As the multi-core CPUs are quite common today, multi-threaded software is 
required to fully utilize such CPUs. Even mobile devices, e.g. cellphones,
feature multi-core CPUs and thus multi-threaded software is increasingly
commonly produced today. This kind of software is hard to test due to the
presence of the non-determinism in thread scheduling. Two runs of the same
program with the same input can lead to a different threads interleaving. This
can cause a different program behaviour for each run. These kinds of bug are
called race conditions. Multi-threaded program's test is also affected by the
scheduler's non-determinism and so it is possible to obtain two different test
results for two test runs. These bugs are also hard to find, as they can occur
only in a single thread interleaving, that can be scheduled only in very specific
circumstances. Also an observation of the program (e.g. run under a debugger or 
run in a different environment) can affect the scheduling and the bug might not
occur.

A lot of effort was put into a development of formal methods during the last few
decades that could replace testing and would help to find more bugs. There are
methods like symbolic execution, bounded model checking and others, that are in
general unsound, however they can help with discovery of the hard-to-find bugs 
(e.g. integer overflow related bugs, memory safety etc.). On the other hand
there are methods like deductive verification, model-checking and others, that
are sound and besides bug-finding they can actually prove absence of a bug. Many
of these methods also support multi-threaded programs, so it is possible to 
deterministically find bugs in a multi-threaded software -- this could be one
of the motivations to replace testing by these methods in the industry.

Despite the promising features of the formal methods, they are not widespread in
the industry and stay mainly within the academic interest. There are several
reasons for that. First of all, techniques like deductive verification are not
automatized and require qualified user interaction. On the other hand, the
automatized techniques does not scale well to real world program. Either they
cannot take an unmodified code and process it (manual annotation is needed, all
language features are not supported), or the verification need an enormous
amount of CPU time and memory for real-world code. Many tools fail to verify
real-world code due to enormous input data domain or complexity in control flow.

One of the tools that aim for verification of the real-world parallel C/C++ code
is \symdivine. It allows user to take an unmodified C/C++ code with
notation of input values and verify it for reachability or \ltl properties. 
To suppress possible state-space explosion caused by input values, it involves
so-called set-based reduction. This reduction is based on symbolic
data representation. This representation heavily uses quantified bit-vector
\smt queries to an \smt solver.

In this thesis we describe and analyse internal \smt machinery of \symdivine,
introduce optimization for this machinery based on the \smt queries caching in
order to speed-up the verification task and help it to scale better. We also
provide implementation of the proposed technique and its experimental evaluation.
