In this chapter, we introduce \symdivine from the user point of view and then
describe its internal architecture. For purposes of this thesis we focus mainly
on selected parts of the \llvm interpreter, \smt data representation and the
related machinery in \symdivine. We omit mainly technical details about \llvm
interpretation and optimization techniques. To more details about the tool we
refer to ToDo.

# About the Tool

\symdivine is a tool for verification of real-world parallel C and C++ programs
with non-deterministic inputs. It is being developed at \paradise Laboratory, at
\FI\ \MU. The tool is built on top of the \llvm framework in order to avoid the
need of modeling and, at the same time, to achieve precise semantics of C and
C++ programming languages. \symdivine is motivated as an extension of purely
explicit model checker \divine\ \cite{BBH+13} that is capable of handling full
parallel C/C++ programs without inputs. \symdivine share the ideology of
\divine -- it aims for bitprecise\footnote{ToDo} verification of parallel C and
C++ programs without modification. To properly handle programs with inputs,
\symdivine relies on control-explicit data-symbolic approach\ \cite{BBH14},
which we detail in the next section.

The tool was originally presented in ToDo(citace Vojta) as a generic platform
for control-explicit data-symbolic state-space exploration. It provided a state
generator from \llvm bit-code and allowed user to specify custom state format
and exploration algorithm. This set-up allowed user to implement wide variety of
verification techniques -- e.g. explicit-state model checking, symbolic
execution or some kind of hybrid technique. Over the years \symdivine
transformed from a generic platform to "out-of-box ready" verification tool by
providing predefined \smt -based state representation and implementation of
algorithms for assertion safety and \ltl properties checking. See
\autoref{fig:workflow} for typical verification work flow of current releases.
Algorithms and store implementation provided in current release were tested in
practise and provide quite good performance. Nevertheless, internal modular
architecture was preserved, so \symdivine can still be used as a platform for
user experiments.

\begin{figure}[!ht]
\resizebox{\textwidth}{!}{
    \begin{tikzpicture}[ ->, >=stealth', shorten >=1pt, auto, node distance=3cm
                       , semithick
                       , scale=0.7
                       , state/.style={ rectangle, draw=black, very thick,
                         minimum height=2em, minimum width = 4em, inner
                         sep=2pt, text centered, node distance = 2em }
                       , font=\sffamily
                       ]

      \node[state, anchor = north west] (cpp) {C/C++};
      \node[state, right = 3em of cpp, rounded corners] (clang) {Clang};
      \node[state, right = 3em of clang] (llvm) {LLVM IR};
      \node[state, right = 3em of llvm, rounded corners] (symdivine) 
      {\symdivine};

      \node[state, above = of symdivine.north, minimum width = 15em] (ltl) 
           {Verified property: reachability, LTL};
      \node[state, right = of symdivine, anchor = west, minimum width = 8em] 
           (valid) {\color{paradisegreen!70!black}OK};
      \node[state, below = of valid, minimum width = 8em] (ce) {\color{red!70!black}Counterexample};

      \path (ltl.south) edge (symdivine.north)
            (cpp) edge (clang)
            (clang) edge (llvm)
            (llvm) edge (symdivine)
            (symdivine) edge (valid) edge[out=0,in=180] (ce)
            ;
    \end{tikzpicture}
    }
    \caption{Typical verification work flow in current version of \symdivine. It
       takes an \llvm bit-code and property specification on input and decides
       whether supplied property does hold or not. If not, an counterexample can
       be produced by the verification algorithm. Input bit-code is usually
       produces by \clang compiler from C or C++ source code, however the user
       can generate it differently.}
    \label{fig:workflow}
\end{figure}

## Input Language Overview

\symdivine is designed to take an \llvm bit-code as an input language and thus
support for C and C++ languages features is mainly reduced to support of \llvm
instruction set. In the current version ToDo \symdivine supports almost all
\llvm instruction except of:

* instructions for symbolic pointer arithmetic

* instructions for pointer casts (simple integer conversions are supported,
  only the real `bitcast` operation is not)

* instructions for floating point arithmetic

To verify program using \symdivine it is necessary that the input \llvm bit-code
is self-contained -- there must not be any call to a function that is not
defined in the bit-code, because behaviour of such functions is unknown to the
tool. This also includes system calls to the underlying operating system. There
are however few exceptions as \symdivine provides intrinsic implementation of
the subset of Pthread library to support multi-threading and also the subset of
functions defined in SV-COMP competition rules ToDo to implement notation for
non- deterministic input.

Following functions from Pthread library are supported:

* `pthread_create`, `pthread_join`, `pthread_create` for thread manipulation

* `pthread_mutex_lock`, `pthread_mutex_unlock` for mutex manipulation

Following functions from SV-COMP notation are supported:

* `__VERIFIER_nondet_{type}` for modelling of non-deterministic input of given
  type

* `__VERIFIER_atomic_begin`, `__VERIFIER_atomic_end` for modelling of atomic 
  sections

This means that the standard C and C++ library is supported if it is linked in
the bit-code form to the input program and used functions do not call any
system call.

Current version of \symdivine does not support heap allocation, so verified
program is forbidden to call `malloc` or use `new` operator. Also dynamic sized
arrays from C99 cannot be handled in the current version of \symdivine.

# Control-Explicit Data-Symbolic Approach

In the standard explicit-state model checking, the state-space graph of the
verified programs is explored by an exhaustive enumeration of its states.
\symdivine basically follows the same idea, but it employs the control-explicit
data-symbolic approach to alleviate the state space explosion caused by the
non-deterministic input values.

When an input read (`__VERIFIER_nondet_{type}` function is called) is
interpreted by an explicit-state model checker, a new successor for every
possible input value has to be produced. This causes tremendous state-space
explosion. It is worth noting these states only differ in a single data field
and thus the same instructions are further applied to all of them (only
branching or `select` instruction can change the control flow). \symdivine can
benefit from this fact. When \symdivine interprets non-deterministic read, only
a single so called *multi-state* is produced. Produced multi-state is composed
of an explicit control flow location and a set of program's memory valuation.

Single multi-state can be viewed as set of purely explicit states (so called
set-based reduction). Thus multi-state space can bring up to exponential size
(and memory) reduction compared to the explicit state-space of the same program
with inputs. The model-checking algorithms present in \symdivine operate on
multi-states. As the multi state-space is up to exponentially smaller and a
single operation application to a multi-state corresponds to an application of
the same operation to a set of explicit states, these algorithms can be much
faster, even though handling multi-states is computational more demanding. This
is the key differentiation compared to the purely explicit approaches. To
illustrate the effect of the set-based reduction, see example of a bit-code and
a corresponding explicit-state space and a multi-state space in
\autoref{fig:statespace}.

Moreover if provide a decision procedures for multi-state equality, it is
possible to adopt existing explicit-state model checking algorithms. This allows
to easily implement standard automata-based \ltl model-checking or perform
safety analysis for non-terminating programs (provided that the multi-state
space is finite).

\begin{figure}[!ht]
    \begin{minted}[xleftmargin=1.5em,linenos=true]{llvm}
%a = call i32 @__VERIFIER_nondet_int()
%b = icmp sge i32 %a, 65535
br i1 %b, label %5, label %6
    \end{minted}  
  
    The code represents a simple \llvm program, where register \texttt{a} is
    initialized with a non-deterministic 32-bit integer, then it is checked
    whether it is greater or equal to a given constant. The result of the check
    is stored to register \texttt{b} and used for branching.

    \begin{center}
    \divine
    
    \resizebox{\textwidth}{!}{
    \begin{tikzpicture}[]
        \tikzstyle{every node}=[align=center, minimum width=1.75cm, minimum height=0.6cm]
        \tikzset{empty/.style = {minimum width=0cm,minimum height=1cm}}
        \tikzset{tnode/.style = {rectangle,draw=black!50,fill=black!10,thick}}
        \tikzset{dots/.style = {draw=none}}
        \tikzset{>=latex}
        \tikzstyle{outer}=[draw, dotted, thick]

        \tikzstyle{wave}=[decorate, decoration={snake, post length=0.1 cm}]
        %divine
        \node [tnode] (s) {\texttt{init}};
        \node [right = 2cm of s] (mid) {};

        \node [tnode, above = -0.25 cm of mid, minimum width=2cm] (s65534){\texttt{a = 65534}};
        \node [tnode, below = -0.25 cm of mid, minimum width=2cm] (s65535){\texttt{a = 65535}};

        \node [dots, above = 0 cm of s65534] (dots1){\LARGE$\vdots$};
        \node [dots, below = -0.2 cm of s65535] (dots2){\LARGE$\vdots$};

        \node [tnode, above = -0.2 cm of dots1, minimum width=2cm] (s0) {\texttt{a = 0}};
        \node [tnode, below = 0 cm of dots2, minimum width=2cm] (sn) {\texttt{a = $2^{32}-1$}};

        \node [tnode, right = 1.5 cm of s65534, minimum width=3.7cm] 
        (s65534_icmp){\texttt{a = 65534; b = 0}};
        \node [tnode, right = 1.5 cm of s65535, minimum width=3.7cm] 
        (s65535_icmp){\texttt{a = 65535; b = 1}};

        \node [dots, above = 0.0 cm of s65534_icmp] (dots1_icmp){\LARGE$\vdots$};
        \node [dots, below = -0.2 cm of s65535_icmp] (dots2_icmp){\LARGE$\vdots$};

        \node [tnode, right = 1.5 cm of s0, minimum width=3.7cm] (s0_icmp) 
        {\texttt{a = 0; b = 0}};
        \node [tnode, right = 1.5 cm of sn, minimum width=3.7cm] (sn_icmp) 
        {\texttt{a = $2^{32}-1$; b = 1}};
           
        \node [empty, left  = 1 cm of s]  (start) {};
        \node [empty, right = 1 cm of s0_icmp] (s0end) {};
        \node [empty, right = 1 cm of s65534_icmp] (s65534end) {};
        \node [empty, right = 1 cm of s65535_icmp] (s65535end) {};
        \node [empty, right = 1 cm of sn_icmp] (snend) {};

        \begin{pgfonlayer}{background}[]
        \node[outer, fit = (s) (s0) (sn) (start) (s0end) (snend) (s0_icmp)] (tool) {};
        \end{pgfonlayer}

        \draw [->] (s.east) -| ($(s.east) !0.3! (s0.west)$) |- (s0.west) node [near end, above=1pt] {\texttt{call}} ;
        \draw [->] (s.east) -| ($(s.east) !0.3! (s65534.west)$) |- (s65534.west) node [near end, above=1pt] {\texttt{call}} ;;
        \draw [->] (s.east) -| ($(s.east) !0.3! (s65535.west)$) |- (s65535.west) node [near end, above=1pt] {\texttt{call}} ;
        \draw [->] (s.east) -| ($(s.east) !0.3! (sn.west)$) |- (sn.west) node [near end, above=1pt] {\texttt{call}} ;

        \draw [->] (s0) -- (s0_icmp) node [midway, above=0pt] {\texttt{icmp}};
        \draw [->] (s65534) -- (s65534_icmp) node [midway, above=0pt] {\texttt{icmp}};
        \draw [->] (s65535) -- (s65535_icmp) node [midway, above=0pt] {\texttt{icmp}};
        \draw [->] (sn) -- (sn_icmp) node [midway, above=0pt] {\texttt{icmp}};

        \draw [wave, ->] (s0_icmp.east) -- (s0end) node [empty, midway, above=2pt] {};
        \draw [wave, ->] (s65534_icmp.east) -- (s65534end) node [empty, midway, above=2pt] {};
        \draw [wave, ->] (s65535_icmp.east) -- (s65535end) node [empty, midway, above=2pt] {};
        \draw [wave, ->] (sn_icmp.east) -- (snend) node [empty, midway, above=2pt] {};

        \draw [wave, ->] (start) -- (s);
    \end{tikzpicture}
    }
    
    \medskip
    
    \symdivine
    \bigskip
    
    \resizebox{\textwidth}{!}{
    \begin{tikzpicture}[]
        \tikzstyle{every node}=[align=center, minimum width=1.75cm, minimum height=0.6cm]
        \tikzset{empty/.style = {minimum width=0cm,minimum height=1cm}}
        \tikzset{tnode/.style = {rectangle,draw=black!50,fill=black!10,thick,align=left}}
        \tikzset{dots/.style = {draw=none}}
        \tikzset{>=latex}
        \tikzstyle{outer}=[draw, dotted, thick]

        \tikzstyle{wave}=[decorate, decoration={snake, post length=0.1 cm}]  
        %symdivine
        \node [tnode] (s_sym) {\texttt{init}};
        \node [tnode, right = 1.0 cm of s_sym, minimum width=2cm] (s_nd_sym) 
        {\texttt{a = \{0,\dots,$2^{32}-1$\}}};

        \node [empty, right = 3.5cm of s_nd_sym] (mid_sym) {};

        \node [tnode, above = -0.45 cm of mid_sym, minimum width=4.6cm] (s1_sym)
        {\texttt{a = \{0,\dots,65534\}}\\\texttt{b = \{0\}}};
        \node [tnode, below = -0.45 cm of mid_sym, minimum width=4.6cm] (s2_sym)
        {\texttt{a = \{65535,\dots,$2^{32}-1$\}}\\\texttt{b = \{1\}}};
            
        \node [empty, left  = 0.5 cm of s_sym]  (start_sym) {};
        \node [empty, right = 0.5 cm of s1_sym] (s1end_sym) {};
        \node [empty, right = 0.5 cm of s2_sym] (s2end_sym) {};

        \begin{pgfonlayer}{background}[]
        \node[outer, fit = (s_sym) (s1_sym) (s2_sym) (start_sym) (s1end_sym) (s2end_sym)] (tool) {};
        \end{pgfonlayer}

        \draw [->] (s_sym.east) -- (s_nd_sym.west) node [midway, above=0pt] {\texttt{call}};

        \draw [->] (s_nd_sym.east) -| ($(s_nd_sym.east) !0.2! (s1_sym.west)$) |- (s1_sym.west) node [near end, above=0pt] {\texttt{icmp}};
        \draw [->] (s_nd_sym.east) -| ($(s_nd_sym.east) !0.2! (s2_sym.west)$) |- (s2_sym.west) node [near end, above=0pt] {\texttt{icmp}};

        \draw [wave, ->] (start_sym) -- (s_sym);
        \draw [wave, ->] (s1_sym) -- (s1end_sym);
        \draw [wave, ->] (s2_sym) -- (s2end_sym);
    \end{tikzpicture}
    }
    \end{center}

    \caption{The figure compares state exploration in the explicit approach of
    \divine and in the control-explicit data-symbolic  approach of \symdivine on
    \llvm program example. From \texttt{init} state \divine explores states for
    every possible value of \texttt{a} ($2^{32}$ values), hence exponentially
    expands state space. In contrast \symdivine approach of symbolic
    representation generates only two different states. One where the condition
    on branching ($a \geq 65535$) is satisfied and the other one where the
    condition is violated. }
    \label{fig:statespace}
\end{figure}

To verify a real-world program an efficient representation of the multi-states
is needed. \symdivine is not linked to a given fixed format of multi-states and
users can supply their own implementation (as is described in detail in the
architecture overview in the section todo). During development of \symdivine
several representations of multi-states were implemented and tested. This
includes representation using binary decisions diagrams (\bdd) or representation
using \smt formulae. \bdd representation performs quite well on artificial
benchmarking programs containing no advanced arithmetic. \smt representation
significantly outperformed the previous one on the real-world programs with more
arithmetic. Support for \bdd representation was dropped in the current version
and the \smt representation is the only one shipped. We describe this
representation in detail in section todo as it an essential preliminary for our
work presented in this thesis.

# Internal architecture

As we mentioned in the previous section, \symdivine was originally developed as
a platform for creating custom tools for the control-explicit approach. Thus the
internal structure is split into clearly separated modules with fixed interface
and each module can easily be replaced by another implementation. The whole tool
is implemented in C++. Each module is represented by a single class. \autoref
{fig:architecture} illustrates components interaction. There are following main
modules in \symdivine:

* \llvm interpreter (responsible for multi-state generation from \llvm bit-code)

* Data stores (implementation of multi-state representation)

* Exploration algorithms

\begin{figure}[!ht]
\begin{center}
\resizebox{0.85\textwidth}{!}{
    \begin{tikzpicture}[ ->, >=stealth', shorten >=1pt, auto, node distance=3cm
                       , semithick
                       , scale=0.7
                       , state/.style={ rectangle, draw=black, very thick,
                         minimum height=2em, minimum width = 4em, inner
                         sep=4pt, text centered, node distance = 2em }
                       , font=\sffamily
                       ]

      \node[state, minimum width = 8em] (inter) {\llvm Interpreter};

      \node[above = 3em of inter] (alg_cent) {};
      \node[state, left = 0.5em of alg_cent, minimum width = 6em] (ltl) {\ltl};
      \node[state, right = 0.5em of alg_cent, minimum width = 6em] (reach) 
      {reachability};
      \node[above = 0.7em of alg_cent] (alg_label) {Algorithms};
      \node[state, left = 4em of ltl] (property) {\ltl formula};

      \node[below = 3em of inter] (data_label) {Data Stores};
      \node[below = 0.7em of data_label] (data_cent) {};
      \node[state, left = 0.5em of data_cent, minimum width = 7em] (expl) 
      {Explicit Store};
      \node[state, right = 0.5em of data_cent, minimum width = 7em] (symb) {\smt
       Store};

       \node[state, right = 3em of symb] (solver) {\smt solver};

      \node[state, left = 6em of inter] (input) {\llvm bit-code};
      \node[state, fit=(ltl) (reach) (alg_label)] 
      (algorithm) {};
      \node[state, fit=(data_label) (expl) (symb)] (state) 
      {};

      \node[state, dotted, label=\symdivine, fit = (algorithm) (state)] (frame) 
      {};

      \path[<->] (inter) edge (algorithm)
                 (inter) edge (state)
                 (symb) edge (solver)
                 ;
      \path[->] (input) edge (inter)
                (property) edge (ltl)
                ;
    \end{tikzpicture}
    }
    \caption{High-level overview of \symdivine architecture. ToDo}
    \label{fig:architecture}
\end{center}
\end{figure}

## \llvm interpreter

Interpreter in \symdivine operates between input \llvm bit-code and a multi-
state space exploration algorithm. It acts as an abstraction layer that provides
explicit program representation in form of a  multi-state space graph to the
exploration algorithms instead of the implicit form (\llvm bit-code). In this
subsection we provide general overview of the interpreter operation and in
detail we describe parts related to the interaction with data store, as
understanding the interaction is essential for our work.

Interpreter is represented by the `Evaluator` class in the source code and
provides a similar interface to the state generators of explicit-state model
checking tools like \divine. After initialization of the interpreter with the
input \llvm bit-code, it provides a reference to so-called working multi-state
(we will refer it as "working copy") and provides several functions that can be
used to modify this working copy. Exploration algorithm then can write a
multi-state to the working copy and use the interface of the interpreter to
modify it and examine it. Following functions are available:

* `initial` function constructs an initial multi-state in the working copy -- a
  multi-state of a program just after the call of the `main` function.

* `advance` function sequentially constructs all possible successors of the
  working copy, caller is notified by a callback function about newly produced
  successor.

* `is_empty` function returns true iff the set of possible memory valuations of
  the working copy is empty.

* `is_error` functions return true iff there is a violated assertion or
  memory corruption (e.g. access beyond array boundaries) in working copy.

* `push_prop_guard` functions filters possible memory valuations of the working
  copy using a given predicate.

This interface allows easy mimicking existing explicit-state model checking
algorithms like simple reachability or automata-based \ltl model checking. A
multi-state corresponds to a set of explicit-states, as we mentioned in the
general tool overview, so the generator related operations in these algorithms
can be up to exponentially faster compared to their explicit-state version.

To allow the interpreter to operate on top of a user-supplied implementation of
a multi-state (here and in a source code referred as "data store"), several
assumptions about the state representation are made:

* control flow location is represented explicitly

* memory layout layer (MML) is provided

* set of functions for data manipulation is provided

We will now discuss each of these assumptions in detail.

The interpreter expects the control flow location in following straightforward
form following the instruction identification in an \llvm bit-code. Each
instruction in an \llvm bit-code can be uniquely identified by a triplet $(f_
{idx}, bb_{idx}, i_{idx})$, where $f_{idx}$ is an index of function in the \llvm
bit-code, $bb_{idx}$ is an index of a basic block in the function and $i_{idx}$
represents index of the instruction in the basic block. As \symdivine supports
multi-threaded programs, a control flow location is kept for each thread. There
is an unique integral identifier assigned to each thread upon its execution.
When the \llvm interpreter needs to reference a thread, it uses this identifier.
When a reference to an instruction is needed, a tuple $(t_{id}, f_{idx}, bb_
{idx}, i_{idx})$ is used, where $t_{id}$ identifies a thread.

To interpret the verified program, unique identification of program's variables
needs to be established. Identification in a similar way as instructions are
identified is not sufficient, because the recursion and nested function calls
might occur and it is necessary to distinguish variables in different calls of
the same function. As \symdivine does not support dynamic memory allocation,
inspiration for variables identification was taken from classical call stack.
When a new block of memory is allocated in an \llvm program (function is called
or an `alloca` instruction is interpreted), new memory segment is created and
assigned to a given function call in a thread or an `alloca` instruction.
Variables are then identified by an index (in source code and in further text
referred as "offset") in this segment. Every instance of a live variable then
can be identified by its segment and offset. Note that the first segment is
reserved for global variables.

Variables naming using segment and offset is required by the interpreter as this
fixed naming allows straightforward implementation of strongly typed pointers,
arrays and structures. Pointers are simply implemented as a pair containing a
segment and a offset. Array of size $n$ are represented as $n$ independent
variables. Since the arrays are strongly typed (`bitcast` instruction is not
supported by \symdivine), pointer arithmetic for arrays can be implemented by
offset manipulation. Similarly structures are implemented as several independent
variables. Since there are no requirements for offset numbering, memory layout
layer, implemented by a data store, allows the interpreter to map variables from
currently executed function to correct offset. To see example of a memory layout
layer, follow
\autoref{sec:symdivine:smtstore}.

Since the set of possible data valuations in a multi-state can be expressed in
many ways, the interpreter relies on the interface provided by the data store.
This interface is designed in a way, that effect of every \llvm instruction and
every intrinsic function definition on given multi-state can be expressed as a
sequence of function application from the interface. The interface is further
described in \autoref{sec:symdivine:arch:datastore}.

Given this set up, implementation of the `advance` function for successor
generation is straightforward. In theory, \symdivine produces successors by an
exhaustive enumeration -- every possible thread interleaving is emitted. This
approach would cause a state-space explosion well known from explicit-state
model checkers that operate on top of \llvm like \divine. To at least partially
alleviate the state-space explosion, the interpreter involves so-called
$\tau$-reduction Todo. In practise the interpreter does not emit every direct
successor, but keeps traversing the multi-state space graph until a visible
action is performed (`load` or `store` on a globally visible variable is
interpreted or an safety property is violated). It effectively squashes effect
of multiple instruction with no visible action to single transition and thus
hides remove unnecessary thread interleaving and produces smaller multi-state
spaces equivalent with the original one (for safety properties and \ltl formulae
with no next operator). For details of implementation we kindly refer to todo
citatce vojta


## Data store \label{sec:symdivine:arch:datastore}

In this subsection we describe an interface of data store, that is used by the
\llvm interpreter to analyse and transform multi-states. To see an example of
possible implementation of this interface, please see
\label{sec:symdivine:smtstore}, where we provide in-depth description of \smt
Store. The interface can be split into following categories: memory layout
layer, transformations and analysis.

The memory layout layer is invoked when the interpreter needs to allocate new
memory or dereference a register or a pointer. Following functions are required:

* `add_segment` function -- given a thread identifier and a list of bit widths,
  constructs a new stack segment and returns segment identifier

* `erase_segment` function -- erases segment and guaranties that values from
  other segments are not affected

* `deref` -- given a thread identifier and a register identifier returns
  identifier of variable in form of segment and offset. If the identifier was a
  pointer, returns identifier to a location pointed by that pointer.

Transformation functions are invoked when the interpreter needs to perform an
arithmetic operation or store value to a memory. Following functions are
required:

* `implement_{op}` -- set of functions, that given three memory locations
  obtained by call to MML, implement a given binary operation (arithmetic,
  bitwise, etc.) using the first two arguments and stores result to the last
  argument.

* `implement_input` -- stores a non-deterministic value to given memory location

* `prune_{op}` -- given a simple relation operator (grater, smaller that, equal
  to, etc.) and two memory locations, removes memory valuations in which the
  relation does not hold.

* `store` and `load` -- takes two memory locations (one points to a pointer,
  second one points to a global scope or a memory allocated by `alloca`) and
  either stores a value from register or loads a value to a register.

Last category of functions are analysis functions:

* `empty` -- returns true iff the set of possible valuations is empty

* `equal` -- given an another multi-state, returns true iff the set of possible
  valuations is empty. Note that there might representations, which equality
  cannot be checked purely by syntactic or memory equality.
  
## Exploration algorithm


# \smt Store \label{sec:symdivine:smtstore}