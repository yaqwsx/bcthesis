# Explicit-State Model Checking

Model checking is a formal method for verification of finite-space systems
against given property \cite{Clarke2000MC}. This check can be performed fully
automatically by a software tool. The core idea of this method is that the whole
state-space of a system can be produced and explored. Usually the system is
composed of multiple processes that can interact with each other. During the
exploration of the system state-space, all interleavings are explored, so a
detection of race conditions is possible. When a property is violated, model
checker can produce a counter-example -- a run that violates the property.

The specification can be expressed as a formula in a temporal logic, like \ltl,
\ctl or \ctls. The system is traditionally specified in a special modelling
language (e.g. ProMeLa in case of \spin \cite{Hol97SPIN}, or DVE in case of
\divine \cite{DiVinE30}). However, this method can be also be used for
verification of computer programs, implying the existence of tools that take a
program source code instead of a special modelling language. Examples of such
tools are CBMC \cite{CBMC} or \divine, that can take a C or C++ code and verify
it against the given property.

Explicit-state model checking considers all possible memory configurations of
the system. This puts a restriction to verified programs -- they cannot read
non-deterministic input values from the outside world. There are, however,
methods like the control-explicit data-symbolic approach \cite{BBH14}, on top of
which is \symdivine build, that can help to solve this issue.

The limiting scalability factor of model checking is the so-called state-space
explosion. With non-determinism in the system (the possibility of resource
acquisition failure, scheduler in multi-threaded systems), the number of
possible runs and consequent size of the state-space, grows exponentially. All
modern model checkers involve techniques for state-space reduction -- e.g.
$\tau+$-reduction \cite{RBB13} in \divine.

# Symbolic Execution

Symbolic execution \cite{Kingsymexec} is another formal verification
technique that, unlike model checking, primarily aims for verification of
programs that can read non-deterministic input values. It does not usually
handle parallel systems well. KLEE \cite{CadarKlee} is an example of a tool for
symbolic execution of C and C++ programs.

Symbolic execution basically executes the program and, instead of obtaining
concrete values of program variables, represents their values symbolically. When
a branching on a non-deterministic value occurs, the computation is split into
two paths -- one where the branching condition was true, the other one where the
branching condition was false. In each branch, a constraint for variable values
is constructed. These constraints form a so-called path-condition. The exploration
produces a symbolic execution tree.

Symbolic execution might not terminate, even on finite-state systems, if an
infinite cycle in the system is present. Symbolic execution is quite wide-spread
and there are many mutations of this technique, e.g. using concrete values to
speed-up the process and using the symbolic part only for synthesis of new
values during branching. Symbolic execution can also be used for automatic
synthesis of tests for software \cite{Kingsymexec}.

# \llvm

\llvm \cite{llvmweb} is a compiler infrastructure. This infrastructure
features tools for optimization and code generation that are independent of
programming language and platform. This is achieved by definition of a custom
intermediate representation -- \llvm IR (also called \llvm bit-code). So-called
compiler front-ends translate the input programming language (C/C++, Haskell,
etc.) in the simplest possible way to \llvm IR. All further optimizations are
performed on top of \llvm IR -- each optimization is written as \llvm to \llvm
transformation and thus optimization may be applied in arbitrary order, even
multiple times. So-called back-ends performs the last step of compilation -- the
translation of \llvm IR to native code for a given platform.

\llvm IR is a static-single-assignment-based low level language similar to
common assembly. It can be represented in three ways: a human-readable form
(`.ll` file), a serialized form for fast machine handling (`.bc` file) or in the
form of an in-memory C++ objects. There is a library that allows easy
manipulation with all the forms of \llvm IR, which is a huge advantage for
software verifiers, as it presents a way to easily take almost any input
programming language relatively effortlessly. In the following text, we will
shortly introduce the most important aspects of \llvm IR.

An \llvm program consists of modules \cite{llvmlangref}. A module contains
functions, global variables and meta-data. Each module is a product of a single
compilation unit or as a product of an \llvm linker. There are two basic
identifiers in \llvm : global identifiers (variables, functions) denoted with
`@` before the name and local identifiers (registers, labels) denoted with `%`
before the name.

Each function consists of  its header (name and parameters definitions) and a
body. The body consists of basic blocks, with each basic block being a sequence
of instructions. Basic blocks cannot contain any branching except the last
instruction. A branching instruction can decide which basic block will be
executed next. A function can use unlimited number of registers to store its
data. These registers are in the SSA form. \llvm instructions operate strictly
on registers, except `load`, `store`, `atomicrmw` and `cmpxchg` instructions,
which can be used for memory manipulation. The address of a register cannot be
taken. To obtain a variable, whose address can be taken, `alloca` instruction
can be used. This instruction takes a size and a type and returns an address of
a memory location. The memory is automatically freed when function returns
(it is usually implemented as a stack allocation).

\llvm is a typed language. There are 4 main groups of types: integral types,
floating point types, pointer types and composed types. Integral types can be
any width and are denoted by `i` and its bit-width -- e.g. `i32` for a typical
integer or `i1` for boolean value. There are two floating point types -- `float`
and `double`. Pointer types are denoted in the same way as in C -- e.g. `i32*`
for a pointer to a 32-bit integer. Composed types can be arrays (`[16 x i32]`) or
structures (`{i32, i8, double}`). Types in \llvm cannot be implicitly cast. To
preform a cast, a special instruction is required.

# Satisfiability Modulo Theories

There many applications in computer science that can benefit from decision
procedure for first-order logic formula satisfiability. Even though there are
solvers for first-order logic \cite{Spass}, many applications do not require
general first-order logic, but rather need satisfiability with respect to a
given background-theory. This background theory usually fixes the domain and
interpretation of predicate and function symbols. A background theory can
usually yield a specialized, more effective decision procedure.

The research field concerned with satisfiability of formulae with respect to
these theories is called *Satisfiability Modulo Theories* (\smt)
\cite{Biere2009}. There are many solvers for various theories: e.g. Z3
\cite{ZZZ}, CVC4 \cite{CVC4} or OpenSMT \cite{opensmt}. Much effort has been put
into standardisation of input to these solvers. This effort resulted in the
SMTLib format \cite{BarFT-SMTLIB} which specifies input language and theories.
In our work, we are mainly interested in \smt for quantified and quantifier-free
version of the FixedSizeBitVectors theory.
