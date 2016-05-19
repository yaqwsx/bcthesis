In this chapter, we introduce \symdivine from the user point of view and then
describe its internal architecture. For purposes of this thesis we focus mainly
on selected parts of the \llvm interpreter, \smt data representation and the
related machinery in \symdivine. We omit mainly technical details about \llvm
interpretation and general optimizations. In many cases, we provide more
in-depth description than \cite{Havel2014thesis}, however, for others, we
kindly refer to that thesis.

# About the Tool

\symdivine is a tool for verification of real-world parallel C and C++ programs
with non-deterministic inputs. It is being developed at \paradise Laboratory, at
\FI\ \MU. It is distributed under MIT licence. Source code can be found at
\url{https://github.com/yaqwsx/SymDIVINE}.

The tool is built on top of the \llvm framework in order to avoid the need of
modelling and, at the same time, to achieve the precise semantics of C and C++
programming languages. \symdivine is motivated as an extension of purely
explicit model checker \divine\ \cite{DiVinE30} that is capable of handling full
parallel C/C++ programs without inputs. \symdivine shares the ideology of
\divine\ --\ it aims for bitprecise\footnote{All operations precisely keep the
semantics of the original program. This is mainly of arithmetic concern --
integers have limited bit-width and overflow on unsigned types is defined.}
verification of parallel C and C++ programs without modification. To properly
handle programs with inputs, \symdivine relies on control-explicit data-symbolic
approach \cite{BBH14}, which we detail in the next section.

The tool was originally presented in \cite{Havel2014thesis} as a generic
platform for control-explicit data-symbolic state-space exploration. It provided
a state generator from \llvm bit-code and allowed the user to specify a custom
state format and an exploration algorithm. This set-up let the user to implement
a wide variety of verification techniques -- e.g. explicit-state model checking,
symbolic execution or some kind of hybrid technique. Over the years, \symdivine
transformed from a generic platform to an "out-of-box ready" verification tool
\cite{spin2016} by providing predefined \smt-based state representation and
implementation of algorithms for assertion safety and \ltl properties checking.
See \autoref{fig:workflow} for typical verification workflow in the current release
\footnote{Current version at the time of writing this thesis is v0.3. Release of
this version is available at
\url{https://github.com/yaqwsx/SymDIVINE/releases/tag/v0.3} and in the
electronic archive submitted with this thesis.}. Algorithms and store
implementation provided in the current release were tested in practise and
provide quite good performance. Nevertheless, the internal modular architecture was
preserved, so
\symdivine can still be used as a platform for user experiments.

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
    \caption{Typical verification workflow in the current version of \symdivine.
       It takes an \llvm bit-code and property specification on input and
       decides whether supplied property does hold or not. If not, a
       counterexample can be produced by the verification algorithm. Input
       bit-code is usually produced by the \clang compiler from C or C++ source
       code, however the user can obtain it differently.}
    \label{fig:workflow}
\end{figure}

## Input Language Overview

\symdivine is designed to take an \llvm bit-code as an input language and thus
support for C and C++ languages features is mainly reduced to support of the
\llvm instruction set. In the current version \symdivine supports almost all
\llvm instructions except of:

* instructions for symbolic pointer arithmetic,

* instructions for pointer casts\footnote{Simple integer conversions are
  supported, only the real `bitcast` operation is not.},

* instructions for floating point arithmetic.

To verify a program using \symdivine, the input \llvm bit-code has to be
self-contained -- there must not be any call to functions that are not defined
in the bit-code. Behaviour of such functions is unknown to the tool and thus
they cannot be verified. This also includes system calls to an underlying
operating system. There are, however, a few exceptions, as \symdivine provides
intrinsic implementation\footnote{Behaviour of these functions is hard-coded in
the interpreter and follows their specification.} of a subset of Pthread library
\cite{pthreads} to support multi-threading and also a subset of functions
defined in SV-COMP competition rules \cite{SVCOMP} to implement a notation for
non-deterministic input.

The following functions from Pthread library are supported:

* `pthread_create`, `pthread_join` and `pthread_create` for thread manipulation

* `pthread_mutex_lock` and `pthread_mutex_unlock` for mutex manipulation

\noindent The following functions from SV-COMP notation are supported:

* `__VERIFIER_nondet_{type}` for modelling a non-deterministic input of a given
  type

* `__VERIFIER_atomic_begin` and `__VERIFIER_atomic_end` for modelling atomic
  sections

\noindent This means that the standard C and C++ library is supported if it is
linked to the input program in the bit-code form and used functions do not call
any system calls.

The current version of \symdivine does not support heap allocation, so the
verified program is forbidden to call `malloc` or use the `new` operator.
Likewise dynamic sized arrays from C99 cannot be handled in the current version
of \symdivine.

# Control-Explicit Data-Symbolic Approach

In the standard explicit-state model checking, the state-space graph of the
verified programs is explored by an exhaustive enumeration of its states.
\symdivine basically follows the same idea, but it employs the control-explicit
data-symbolic approach to alleviate the state space explosion caused by the
non-deterministic input values.

When an input read (`__VERIFIER_nondet_{type}` function is called) is
interpreted by an explicit-state model checker, a new successor for every
possible input value has to be produced. This causes a tremendous state-space
explosion. It is worth noting that these states only differ in a single data
field and thus the same instructions are further applied to all of them (only
branching or the `select` instruction can change the control flow). \symdivine
can benefit from this fact. When \symdivine interprets non-deterministic read,
only a single so-called *multi-state* is produced. The produced multi-state is
composed of an explicit control flow location and a set of program's memory
valuation.

A single multi-state can be viewed as a set of purely explicit states (so-called
set-based reduction, we kindly refer to \cite{Havel2014thesis} for formal
definition). As a result, multi-state space can bring up to exponential size
(and memory) reduction compared to the explicit state-space of the same program
with inputs. The model-checking algorithms present in \symdivine operate
exclusively on multi-states. As the multi state-space is up to exponentially
smaller and a single operation application to a multi-state corresponds to an
application of the same operation to a set of explicit states, these algorithms
can be much faster, even though handling multi-states is computationally more
demanding. This is the key differentiation compared to the purely explicit
approaches. To illustrate the effect of the set-based reduction, see an example
of a bit-code and the corresponding explicit-state space and a multi-state space
in \autoref{fig:statespace}.

Moreover, if we provide a decision procedures for multi-state equality, it is
possible to adopt existing explicit-state model checking algorithms. This allows
easy implementation of standard automata-based \ltl model-checking or perform
safety analysis for non-terminating programs (provided that the multi-state
space is finite).

\begin{figure}[!ht]
    \begin{minted}[xleftmargin=1.5em,linenos=true]{llvm}
%a = call i32 @__VERIFIER_nondet_int()
%b = icmp sge i32 %a, 65535
br i1 %b, label %5, label %6
    \end{minted}  
  
    The code represents a simple \llvm program, where register \texttt{a} is
    initialized with a non-deterministic 32-bit integer, then is checked whether
    it is greater or equal to a given constant. The result of the check is
    stored to register \texttt{b} and used for branching.

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
    \divine and in the control-explicit data-symbolic  approach of \symdivine on an
    \llvm program example. From \texttt{init} state \divine explores states for
    every possible value of \texttt{a} ($2^{32}$ values), hence exponentially
    expands the state space. In contrast, the \symdivine approach of symbolic
    representation generates only two different states. One where the condition
    on branching ($a \geq 65535$) is satisfied and the other one where the
    condition is violated. }
    \label{fig:statespace}
\end{figure}

To verify a real-world program, an efficient representation of the multi-states
is needed. \symdivine is not linked to a given fixed format of multi-states and
users can supply their own implementation (as described in detail in
\autoref{sec:architecture}). During development of \symdivine several
representations of multi-states were implemented and tested. This includes
representation using binary decisions diagrams (\bdd) or representation using
\smt formulae. \bdd representation performs quite well on artificial
benchmarking programs containing no advanced arithmetic. \smt representation
significantly outperformed the previous one on real-world programs with more
arithmetic. Support for \bdd representation was dropped in the current version
and the \smt representation is the only one shipped. We describe this
representation in detail in \autoref{sec:symdivine:smtstore}, as it an essential
preliminary for our work presented in this thesis.

# Internal Architecture\label{sec:architecture}

As we mentioned in the previous section, \symdivine was originally developed as
a platform for creating custom tools for the control-explicit data-symbolic
approach. Thus the internal structure is split into clearly-separated modules
with fixed interface and each module can easily be replaced by another
implementation. The whole tool is implemented in C++. Each module is represented
by a class. \autoref {fig:architecture} illustrates components
interaction. There are following main modules in \symdivine:

* the \llvm interpreter (responsible for multi-state generation from \llvm bit-code),

* data stores (implementation of multi-state representation),

* exploration algorithms.

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
    \caption{High-level overview of \symdivine architecture. Nested boxes correspond to interfaces and their concrete implementations.}
    \label{fig:architecture}
\end{center}
\end{figure}

## \llvm Interpreter \label{sec:arch:inter}

The interpreter in \symdivine operates between input \llvm bit-code and a
multi-state space exploration algorithm. It acts as an abstraction layer that
provides explicit program representation in the form of a multi-state space
graph instead of the implicit one to the exploration algorithms. In this
subsection we provide a general overview of the interpreter operation and we
describe parts interacting with data store in detail, as understanding the
interaction is essential to our work.

The interpreter is represented by the `Evaluator` class in the source code and
provides a similar interface to the state generators of explicit-state model
checking tools like \divine. After initialization of the interpreter with an
input \llvm bit-code, it provides a reference to so-called working multi-state
(we will refer to it as the "working copy") and provides several functions that
can be used to modify this working copy. Exploration algorithm then can then
write a multi-state to the working copy and use the interface of the interpreter
to modify it and examine it. The following functions are available:

* `initial` function constructs an initial multi-state in the working copy -- a
  multi-state of a program just after the start of the main thread and the call
  of the `main` function.

* `advance` function sequentially constructs all possible successors of the
  working copy. The caller is notified about newly produced successor by a
  callback function.

* `is_empty` function returns true if the set of possible memory valuations of
  the working copy is empty.

* `is_error` function returns true if there is a violated assertion or a memory
  corruption (e.g. access beyond array boundaries) in the working copy.

* `push_prop_guard` function filters possible memory valuations of the working
  copy using a given predicate.

\noindent This interface allows for easy mimicking existing explicit-state model
checking algorithms like simple reachability or automata-based \ltl model
checking. A multi-state corresponds to a set of explicit-states, as we mentioned
in the general tool overview, so the generator-related operations in these
algorithms can be up to exponentially faster compared to their explicit-state
version.

To allow the interpreter to operate on top of a user-supplied implementation of
a multi-state (here and in a source code referred to as *data store*), several
assumptions about the state representation are made:

* control flow location is represented explicitly,

* memory layout layer (MML) is provided,

* set of functions for data manipulation is provided.

\noindent We will now discuss each of these assumptions in detail.

The interpreter expects the control flow location in a straightforward form
following the instruction identification in an \llvm bit-code. Each instruction
in an \llvm bit-code can be uniquely identified by a triplet $(f_ {idx},
bb_{idx}, i_{idx})$, where $f_{idx}$, $bb_{idx}$ and $i_{idx}$ are indices of
function in the \llvm bit-code, a basic block in the function and the
instruction in a basic block, respectively. As \symdivine supports
multi-threaded programs, a control flow location is kept for each thread. There
is a unique integral identifier assigned to each thread upon its execution. To
represent control flow state of a multi-thread program with function calls,
\symdivine keeps a stack of instruction identifiers for every thread.

To interpret the verified program, a unique identification of program's
variables also needs to be established. Identification similar to the way as
instructions are identified is not sufficient, because recursion and nested
function calls might occur and it is necessary to distinguish variables in
different calls of the same function. As \symdivine does not support dynamic
memory allocation, inspiration for variable identification was taken from the
classical call stack. When a new block of memory is allocated in an \llvm
program (function is called or an `alloca` instruction is interpreted), a new
memory segment is created and assigned to the operation (function call or the
`alloca` instruction). Each automatic variable in the function body or an
element of array (in case of the `alloca` instruction) is then assigned an index
(in source code and in further text referred to as *offset*) in this segment.
Every instance of a live variable can then be identified by its segment and
offset. Note that the first segment is reserved for global variables.

Variable naming using segment and offset is required by the interpreter as this
fixed naming allows straightforward implementation of strongly typed pointers,
arrays and structures. Pointers are simply implemented as a pair containing a
segment and an offset. An array of size $n$ is represented as $n$ independent
variables. Since the arrays are strongly typed (the `bitcast` instruction is not
supported by \symdivine), pointer arithmetic for arrays can be implemented as
offset manipulation. Similarly, structures are implemented as several
independent variables. Since there are no requirements for the offset numbering,
memory layout layer, implemented by a data store, allows the interpreter to map
variables from currently executed function to a correct offset. To see example
of a memory layout layer, follow \autoref{sec:symdivine:smtstore}.

Since the set of possible data valuations in a multi-state can be expressed in
many ways, the interpreter relies on the interface provided by the data store.
This interface is designed in such a way, that the effect of every \llvm
instruction and every intrinsic function definition on a given multi-state can
be expressed as a sequence of function application from the interface. The
interface is further described in \autoref{sec:symdivine:arch:datastore}.

Given this set up, the implementation of the `advance` function for successor
generation is straightforward. In theory, \symdivine produces successors by an
exhaustive enumeration -- every possible thread interleaving is emitted. This
approach would cause a state-space explosion well-sknown from explicit-state
model checkers that operate on top of \llvm like \divine. To at least partially
alleviate the state-space explosion, the interpreter involves the so-called
$\tau$-reduction\cite{RBB13}. In practice the interpreter does not emit every
direct successor, but keeps traversing the multi-state space graph until a
visible action is performed (`load` or `store` on a globally visible variable is
interpreted or a safety property is violated). It effectively squashes the
effect of multiple instructions with no visible action to single transition and
thus removes unnecessary thread interleavings and produces smaller multi-state
spaces equivalent with the original one (for safety properties and \ltl formulae
with no next operator). For details of implementation we kindly refer to
\cite{Havel2014thesis}.

To illustrate the interpreter operation, we present \autoref{fig:codegeneration}
and \autoref{fig:generation}. The first figure shows an example of a simple C
code and the corresponding \llvm bit-code. The second figure shows a multi-state
space graph that is produced by the interpreter if the bit-code from
\autoref{fig:codegeneration} is supplied as the input.


\begin{figure}[!ht]
    \begin{minted}[xleftmargin=1.5em,linenos=true]{C}
volatile int a;
int main() {
    a = __VERIFIER_nondet_int();
    while(1) {
        int b = __VERIFIER_nondet_int();
        if (b < a) { a = b; }
        if (a == 42) { break; }
    }
    return 0;
}
    \end{minted}
    \begin{minted}[xleftmargin=1.5em,linenos=true]{llvm}
@a = common global i32 0, align 4
; Function Attrs: nounwind uwtable
define i32 @main() #0 {
  %1 = tail call i32 (...)* @__VERIFIER_nondet_int() #2
  store volatile i32 %1, i32* @a, align 4, !tbaa !1
  br label %2

; <label>:2                                ; preds = %7, %0
  %3 = tail call i32 (...)* @__VERIFIER_nondet_int() #2
  %4 = load volatile i32* @a, align 4, !tbaa !1
  %5 = icmp slt i32 %3, %4
  br i1 %5, label %6, label %7

; <label>:6                                ; preds = %2
  store volatile i32 %3, i32* @a, align 4, !tbaa !1
  br label %7

; <label>:7                                ; preds = %6, %2
  %8 = load volatile i32* @a, align 4, !tbaa !1
  %9 = icmp eq i32 %8, 42
  br i1 %9, label %10, label %2

; <label>:10                               ; preds = %7
  ret i32 0
}
    \end{minted}  
  
    \caption{Example of a very simple C code and the corresponding \llvm
    bit-code obtained as a result of a compilation with \clang with O2
    optimizations. The produced bit-code should be simple enough to be
    understandable even without a deep knowledge of \llvm. Note that variable
    \texttt{a} was marked as \texttt{volatile} and thus the compiler cannot
    optimize out any load or store operations to/from this variable. See
    \autoref{fig:generation} for the corresponding multi-state space. }
    
    \label{fig:codegeneration}
\end{figure}

\begin{figure}[!ht]
\begin{center}
\resizebox{0.9\textwidth}{!}{
    \begin{tikzpicture}[ ->, >=stealth', shorten >=1pt, auto, node distance=3cm
                       , semithick
                       , scale=0.7
                       , state/.style={ rectangle, draw=black, very thick,
                         minimum height=2em, minimum width = 13em, inner
                         sep=6pt, text centered, node distance = 2em, align = left,  rounded corners }
                       , font=\sffamily
                       ]

      \node[state, label = initial] (initial)
            {PC: 4 \\
             @a  $\in \{-2^{32},\dots, 2^{32}-1\}$\\
             \%1 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%3 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%4 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%5 $\in$ \{$0,1$\}\\
             \%8 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%9 $\in$ \{$0,1$\}};

      \node[state, right = 6em of initial] (2)
            {PC: 6 \\
             @a  = \%1\\
             {\color{red}\%1 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}}\\
             \%3 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%4 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%5 $\in$ \{$0,1$\}\\
             \%8 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%9 $\in$ \{$0,1$\}};

      \node[state, below = 1.5 em of 2] (3)
            {PC: 11 \\
             {\color{red}@a  = \%1}\\
             \%1 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             {\color{red}\%3 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}}\\
             {\color{red}\%4 = @a}\\
             \%5 $\in$ \{$0,1$\}\\
             \%8 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%9 $\in$ \{$0,1$\}};

      \node[state, below = of 3] (4)
            {PC: 20 \\
             @a  = \%1\\
             \%1 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             {\color{red}\%3 $\in$ \{@a$,\dots, 2^{32}-1$\}}\\
             \%4 = @a\\
             {\color{red}\%5 = 0}\\
             {\color{red}\%8 = @a}\\
             \%9 $\in$ \{$0,1$\}};

      \node[state, left = 6em of 3] (5)
            {PC: 16 \\
             {\color{red}@a  = \%3}\\
             \%1 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             {\color{red}\%3 $\in$ \{$-2^{32},\dots, $@a$_{prev}-1$\}}\\
             {\color{red}\%4 = @a}\\
             {\color{red}\%5 = 1}\\
             \%8 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%9 $\in$ \{$0,1$\}};

      \node[state, below = of 5] (6)
            {PC: 20 \\
             @a  = \%3\\
             \%1 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%3 $\in$ \{$-2^{32},\dots, $@a$_{prev}-1$\}\\
             \%4 = @a\\
             \%5 = 1\\
             {\color{red}\%8 = @a}\\
             \%9 $\in$ \{$0,1$\}};

      \node[state, below = of 4] (7)
            {PC: end \\
             @a  = \%1\\
             \%1 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%3 $\in$ \{@a$,\dots, -2^{32}-1$\}\\
             \%4 = @a\\
             \%5 = 0\\
             \%8 = @a\\
             {\color{red}\%9 $=1$}};

      \node[state, below = of 6] (8)
            {PC: end \\
             @a   =\%3\\
             \%1 $\in$ \{$-2^{32},\dots, 2^{32}-1$\}\\
             \%3 $\in$ \{$-2^{32},\dots, $@a$_{prev}-1$\}\\
             \%4 = @a\\
             \%5 = 1\\
             \%8 = @a\\
             {\color{red}\%9 $=1$}};

      \path[->] (initial) edge (2)
                (2) edge (3)
                (3) edge node [midway, above=0pt] {$\%3<\%4$} (5)
                (3) edge node [midway, right=0pt] {$\%3\geq \%4$} (4)
                (4.east) edge[bend right] node [right=0pt] {$\%8\neq 42$} (3.east)
                (5) edge (6)
                (6) edge node [midway, right=0pt] {$\%8=42$} (8)
                (4) edge node [midway, right=0pt] {$\%8=42$} (7)
                (6.north east) edge node [midway, above=7pt] {$\%8\neq 42$} (3.south west)
                ;
    \end{tikzpicture}
    }
    \caption{Multi-state space corresponding to the code from
    \autoref{fig:codegeneration}. As there are no nested function calls, we used
    simple naming according to variable and register names in the \llvm bit-
    code. Program counter (PC) is expressed as a line number of instructions
    that is going to be interpreted next to make the scheme easier to read. Note
    the $\tau$-reduction in action, where multiple globally invisible actions
    are squashed together. To make the schematic even more easy to read, we
    highlighted fields that have been modified by a transition and we also added
    labels to edges, to make clear which action caused a given transition. If
    multiple threads were involved, all possible context switches would occur on
    every transition. Also, please note that to express the valuations set, it
    was necessary to refer to the value of \texttt{a} from previous state. We
    marked it as a$_{prev}$. }
    \label{fig:generation}
\end{center}
\end{figure}


## Data Store \label{sec:symdivine:arch:datastore}

In this subsection we describe an interface of a data store that is used by the
\llvm interpreter to analyse and transform multi-states. To see an example of a
possible implementation of this interface, please see
\autoref{sec:symdivine:smtstore}, where we provide in-depth description of \smt
Store. Each data store keeps the explicit part of a state and the symbolic
(data) part. We omit description of the explicit part of state as its
implementation is trivial. The interface can be split into following categories:
memory layout layer, transformations and analysis.

To present the interface formally, we define a set of possible memory valuations
as a function $v: V \rightarrow 2^B$, where $V$ is a finite set of program
variables and $B$ is a set of all bit-vectors. $v$ also follows that for all $y
\in v(x), x \in V$ the bit-width of $y$ matches the bit width of $x$ declared in
the \llvm bit-code.

The memory layout layer is invoked when the interpreter needs to allocate new
memory or dereference a register or a pointer. The following functions are
required:

* `add_segment(bws)` function -- given a thread identifier and a list of bit
  widths `bws`, constructs a new stack segment for these variables and returns
  its identifier. Formally speaking, the set of variables $V$ is extended,
  $v(x)$ for newly-added $x$ is undefined.

* `erase_segment(id)` function -- erases segment and guarantees that valuation
  of variables from other segments is not changed. Formally, the set of
  variables $V$ is reduced. Value of $v(x)$ for all $x$ that were not in
  the removed segment also stays the same.

* `deref(tid, id)` -- given a thread identifier and a register identifier from
  \llvm bit-code, it returns an identifier of a variable in the form of segment
  and offset. If the identifier was a pointer, it returns an identifier to a
  location pointed to by that pointer. Only values from the global scope or the
  currently called function in the given thread are allowed as arguments.

\noindent Transformation functions are invoked when the interpreter needs to
perform an arithmetic operation or store value to a memory. The following
functions are required:

* `implement_{op}(a, b, c)` -- set of functions that, given three memory
  locations obtained by call to MML, implement a given binary operation
  (arithmetic, bitwise, etc.) using `a` and `b` as arguments and storing the
  result to `c`. Formally, `implement_{op}` changes $v$ to $v'$ such that $v'(x)
  = \{ x \texttt{ op } y \mid x \in v(\texttt{a}), y \in(\texttt{b})\}$ if
  $x=\texttt{c}$, otherwise $v'(x) = v(x)$.

* `implement_input(a)` -- stores a non-deterministic value to given memory
  location. Formally, `implement_input` changes $v$ to $v'$ such that $v'(x) =
  \{ b \mid b \mbox{ is a bit-vector of bit-with corresponding to bit-width of }
  x \}$ if $x=\texttt{a}$, otherwise $v'(x) = v(x)$

* `prune_{op}(a, b)` -- given a simple relation operator (grater, smaller that,
  equal to, etc.) and two memory locations, it removes memory valuations in
  which the relation does not hold.

* `store(r, p)` and `load(r, p)` -- given a register and a pointer\footnote{Note
  that \texttt{store} can also take a constant instead of  aregister. As it is a
  technical detail, we omit this variant in the text.}, it either stores a value
  from register to the memory pointed to by the pointer or loads a value to a
  register from memory pointed to by the pointer. Formally, `store` changes $v$
  to $v'$ such that $v'(x) = v(r)$ if `p` points to $x$, otherwise $v'(x) =
  v(x)$. `load` operation is defined symmetrically.

\noindent The last category are analysis functions used mainly by exploration
algorithms to construct a set of known multi-states and produce a product with
an automaton:

* `empty(a)` -- returns true if the set of possible valuations of `a` is empty.
  Formally, returns true if and only if there is an $x$ such that
  $v_a(x)=\emptyset$.

* `equal(A, B)` -- given two multi-states, returns true if the program counter
  of both states is the same and the sets of possible valuations are the same.
  Formally, returns $v_A=v_B$. Note that the sets of program variables $V_A$
  and $V_B$ are the same, as \symdivine does not support heap allocation and
  the program counters are equal. Also note that there might be representations,
  whose equality cannot be checked purely by syntactic or memory equality, as we
  show in an example \autoref{sec:symdivine:smtstore}.

* `get_explicit_part` -- returns an encoded explicitly represented part of the
  multi-state in the form of a binary blob. If two multi-states are equal to
  each other, both blobs from the multi-states have to be the same.

* `less_than` -- if there is an ordering defined on the multi-state
  representation, this function can be provided (and thus an algorithm can use a
  tree set to represent a set of multi-states)

\noindent There were several implementations of data store developed. A short
summary of them follows. Note that not all of them are distributed in the
current release of \symdivine as they were replaced by a more efficient one, or
their development and support was discontinued.

* Explicit store -- represents only a single possible memory valuation, not a
  set of valuations. Usage of this store "degrades" \symdivine to a purely
  explicit-state model checker. This store is used for implementation of the
  explication optimization to reduce number of multi-state equality test during
  state space exploration. As this optimization is not important for our thesis,
  we kindly refer to cite{Havel2014thesis} for further detail.

* \bdd store -- \bdds are used to represent a set of possible memory valuations.
  There are algorithms for computing binary arithmetic and logic operations for
  \bdd \cite{bdd}, so the implementation of a store is straightforward
  -- for every program's variable there is a single \bdd. An equality check of two
  \bdd s is a cheap operation, as they feature canonical representation. However,
  the construction of a \bdd for arithmetic operations (e.g. multiplication) is
  quite expensive. This kind of store failed to verify even small examples due
  to the high complexity \cite{Havel2014thesis}. Thus, development of this store
  was discontinued

* \smt store -- uses an \smt formula to represent a set of possible memory
  valuations. To decide whether two representations describe the same set of
  valuations, an \smt solver for quantified bit-vector theory is used. For
  further description of this store, follow \autoref{sec:symdivine:smtstore},
  where we describe this store in detail. The store is used as the primary one
  in the current release of \symdivine.

* Empty store -- does not represent any memory valuations and only a collects
  sequence of transformations applied to the store. This is not useful for any
  verification technique, however, it can be used to translate an \llvm bit-code
  into different kinds of formalisms. See next section where we describe this
  process in more detail.

## Exploration Algorithms

On top of the \llvm interpreter and a data store it is easy to implement an
algorithm for state space exploration. The algorithm is usually the only thing
user interacts with. Taken all inputs from the user (\llvm bit-code, property,
exploration strategy etc.), it usually instantiates an interpreter, asks for an
initial state and, using the `advance` function of the interpreter, it builds a
set of known multi-states or even the full multi-state space graph.

As a multi-state is required to provide a procedure for equality of two
multi-states, it is possible to represent a set of multi-states. A set
representation using only a an equal operation would not scale well to
real-world program sizes for obvious reasons. Note that a traditional hash-set
used in explicit-state model checker cannot be used as there can be a
multi-state representation that doesn't have a canonical form (e.g. \smt store).
Thus, \symdivine tries to benefit from having an explicit control flow is
mandatory for every data store implementation. A typical set of multi-states is
implemented as follows: there is a hash map containing a list of symbolic parts
of the multi-states for every explicit part of the multi-states. When a new
element is inserted to the set, list of the symbolic parts corresponding to the
explicit part is recalled and then every symbolic part from the list is tested
for equality. If an equal symbolic part is found, procedure ends; otherwise new
symbolic part is put at the end of the list. This optimization significantly
reduces the number of calls to the equality procedure, however, it is still
possible to obtain a significant number of symbolic parts per control flow
location. If a multi-state representation allows to implement the `less_than`
procedure, it is possible to replace a linear search by binary search and thus
further optimize the set representation.

Using various combinations of algorithms and data stores, \symdivine can serve
as a multi-purpose tool. During development of \symdivine, experiments with the
following combinations were performed:

* \smt or \bdd store combined with an algorithm for reachability. This
  combination produces a model-checker for safety properties that can handle
  input values. This approach was originally introduced in
  \cite{Havel2014thesis}.

* \smt or \bdd store combined with a standard algorithm for automata-based
  \ltl model-checking. During the verification, negation of specification \ltl
  formula is converted to a \buchi automaton and during the successors generation
  procedure a product with the automaton is produced. A test for atomic
  propositions that can refer to global variables of the program is
  implemented using the `prune` operation of the store. It filters-out memory
  valuations that violate the atomic proposition -- see \autoref{fig:ltl}. This
  approach was originally implemented in \cite{BHB14} and further improved in
  \cite{spin2016}.

* Explicit store combined with reachability or an \ltl algorithm on input
  programs with no non-deterministic input produces a standard explicit-state
  model checker.

* \smt or \bdd store combined with simple exploration without tracking the set
  of known multi-states yields in a symbolic execution.

* Empty store in combination with reachability can be used to convert \llvm
  bit-code to an artificial modelling language. Thus, tool like nuXmv
  \cite{nuxmv}, that does not support \llvm as an input formalism, can be
  used to verify properties of an \llvm bit-code. When running the reachability,
  the empty store produces one state per each reachable control flow location
  and collects sequence of transformations applied to the state and transition
  guard -- constructs a non-deterministic guarded transition system. After
  exploration, this transition system is translated to desired modelling
  language. This usage of \symdivine was introduced in \cite{BHB14}.

\begin{figure}[!ht]
\begin{center}
\resizebox{\textwidth}{!}{
    \begin{tikzpicture}[ ->, >=stealth', shorten >=1pt, auto, node distance=1.5cm
                       , semithick
                       , scale=0.7
                       , font=\sffamily
                       , stateprog/.style={ rectangle, draw=black, very thick,
                         minimum height=2em, minimum width = 10em, inner
                         sep=6pt, text centered, node distance = 2em, align = left,  rounded corners }
                       ]
        \node[initial, state] (1) {1};
        \node[state, above right = of 1] (2) {2};
        \node[state, right = of 1] (3) {3};
        \node[state, below right = of 1] (4) {4};

        \node[stateprog, right = of 3, label = (A)] (p1)
            {PC: 1 \\
             BA: 1 \\
             a $\in \{0,\dots, 2^{32}-1\}$};
        \node[stateprog, above right = of p1, label = (B)] (p2)
            {PC: 1 \\
             BA: 2 \\
             a $\in \emptyset$};
        \node[stateprog, right = of p1, label = (C)] (p3)
            {PC: 1 \\
             BA: 3 \\
             a $=0$};
        \node[stateprog, below right = of p1, label = (D)] (p4)
            {PC: 1 \\
             BA: 4 \\
             a $\in \{1, 2^{32}-1\}$};

        \path[->]
                (1) edge node [midway, left=0pt] {$a < 0$} (2)
                (1) edge node [midway, above=0pt] {$a = 0$} (3)
                (1) edge node [midway, left=0pt] {$a > 0$} (4)
                (p1) edge [dashed] (p2)
                (p1) edge [dashed] (p3)
                (p1) edge [dashed] (p4)
                ;
    \end{tikzpicture}
    }
    \caption{Illustration of a multi-state space generation in an automata based
    \ltl model checking. The \ltl exploration algorithm takes a \buchi
    automaton (a subset of such a automaton is shown in the left). The
    generation procedure works as follows: state that is being explored is
    loaded into the interpreter and a new successor (state A) is produced. The
    state contains a program counter, a \buchi automaton state and a set of
    possible data valuations. The product (states B, C and D) is generated by
    taking all possible transitions of the automaton from  a given state by
    pruning the set of valuations. All non-empty states (C, D) are then emitted
    as successors of the explored state. }
    \label{fig:ltl}
\end{center}
\end{figure}


# \smt Store\label{sec:symdivine:smtstore}

In this section we closely look at the implementation of \smt Store, as
understanding of its internals is essential for our work. First, we describe the
store from a theoretical point of view and then we closely look at the actual
implementation, which features several optimizations and thus slightly differs
from the theoretical model.

## Theoretical Model

\smt store uses a representation described in \cite{BBH14}. A quantifier-free
first-order bit-vector \smt formula $\varphi$ called *path condition* is used
for description of the possible memory valuations set defined in
\autoref{sec:symdivine:arch:datastore}. The set of program variables $V$
(defined in \autoref{sec:symdivine:arch:datastore}) can be mapped to the set of
the free variables in the path condition (in a way we describe later in the
text). Program variables can be sequentially assigned different values during a
single program run. To distinguish different values assigned to a variable, a
so-called *variable's generation* is used. For each assignment to a program
variable, a new variable in formula is created (with incremented generation
number). Thus, the set of variables in formula is a subset of $V \times
\mathbb{N}$ and we can denote a formula variable as a pair $(v, g)$, were $v$ is
a program variable from $V$ and $g$ is its generation. The mapping from formula
variables to program variables is easy -- every program variable $v$ maps to
formula variable $(v, g)$ with the maximum generation $g$. The set of all models
of path condition defines the valuation function $v$.

Implementing the data store interface using path condition is performed in the
following way (as described in \cite{Havel2014thesis}): when we refer to a
formula variable, we refer to the latest generation. We also assume implicit
mapping of program variables to formula variables (when we use program variable
in formula, we assume it is translated to formula variable with maximum
generation).

* `add_segment(bws)` and `erase_segment(id)` functions do not modify the path
  condition, only meta information used for implementation is modified.

* `implement_{op}(a, b, c)` on state with a path condition $\varphi$ leads to a
  new path condition: $\varphi \wedge \left((\texttt{c}, g + 1) = \texttt{a op
  b}\right)$.

* `implement_input(a)` increases generation of `a` and does not modify path
  condition, as a variable with no constrains models a non-deterministic value.

* `prune_{op}(a, b)` on a state with a path condition $\varphi$ leads to a new
  path condition: $\varphi \wedge \left(\texttt{a op b}\right)$.

* `store(r, p)` and `load(r, p)` on a state with w path condition $\varphi$ leads to
  a new path condition: $\varphi \wedge \left((\texttt{p}, g + 1) =
  \texttt{r}\right)$ in case of the `store` instruction, `load` instruction is
  defined in a symmetrical manner.

* `empty` returns true if and only if the path condition is not satisfiable.
  Satisfiability is decided using an \smt solver.

* `equal(A, B)` returns true if and only if the path condition $\varphi$ of `A`
  and path condition $\psi$ of `B` represent the same set of possible
  valuations. There is no canonical form of \smt formulae, thus two different
  formulae can describe the same set and it is not possible to decide equality
  using purely simple syntactic equality. Note that there also cannot be any
  `less_than` function implemented for this data store. A quantified bit-vector
  \smt query is made to a solver in order to decide the equality. `equal(A, B)`,
  returns true if and only if:
  \begin{equation}
    \neg \operatorname{notsubseteq}(\texttt{A}, \texttt{B}) \wedge
        \neg\operatorname{notsubseteq}(\texttt{B}, \texttt{A}) \nonumber
  \end{equation}
  is satisfiable. $\operatorname{notsubseteq}(\texttt{A}, \texttt{B})$ is a
  short-cut for:
  \begin{equation}
    \exists b_0,\dots,b_n\ldotp \psi \wedge \forall a_0,\dots,a_n\ldotp \varphi
    \implies
        \left(
            \bigvee \left(a_i \neq b_i\right)
        \right) \nonumber
  \end{equation}
  where $a_0,\dots,a_n$ denotes the program variables in `A` and $b_0,\dots,b_n$
  denotes the program variables in `B`. Intuitively, notsubseteq looks for a
  valuation in `A` that is not present in `B`.

Given the implementation of the operations, we can now easily illustrate the
need for different variable generations. Consider the following example of an
\llvm bit-code:

\begin{minted}[xleftmargin=1.5em,linenos=true]{llvm}
store i32 5, i32* %a, align 4
%2 = load i32* %a, align 4
store i32 %2, i32* %b, align 4
store i32 42, i32* %a, align 4
\end{minted}

This piece of bit-code stores constant 5 to `%a`, then assigns the value of `%a`
to `%b`. The last operation stores constant 42 to `%a`. With no generations, the
last store operation would change both values of `%a` and `%b`, so it is
necessary to keep track of each variable's history.

## Implementation\label{subsec:symdivine:smt:impl}

To achieve a better performance of \smt store, several optimization to the
purely theoretical approach are made. In this section we first describe the
implementation of meta information that is needed to correctly build a path
condition. Then we describe the optimization of path condition building and the
evaluations of the `empty` and `equal` operations.

\symdivine uses the Z3 \smt solver \cite{ZZZ} to decide the satisfiability of
both quantifier-free and quantified \smt queries. In order to allow easy usage
of other solvers, \smt store relies on the internal formulae representation. The
path condition is stored in this internal representation. When an \smt query is
needed, the internal representation is translated to solver's specific format.

To correctly and effectively build a path condition, preservation of the set of
program variables, their mapping to formula variables and their generations is
needed. Also, as we described in section \autoref{sec:arch:inter}, the
interpreter requires that data store provides MML -- thus a mapping among
variables in \llvm bit-code and program variables (where multiple calls of the
same function are allowed) needs to be established. We remind that program
variables are required to be identified by a segment and an offset.

To perform these mappings, \smt store takes advantage of the required
segment-offset program variable identification and thus keeps a set of segments
with variables and a mapping of call stack frames to these segments. Note that
this mapping is not canonical -- different thread interleaving can lead to a
different mapping. Each segment contains a list of variables (information about
the highest generation, bit-width, etc.). See \autoref{fig:mapping} for an
illustration of this mapping.

As the set of segments is usually quite small, frequently accessed and changed,
an implementation using a dynamic-sized array and a free-list was chosen. Thus
the segment identifiers are re-used and the same segment in two different
states can be mapped to a different stack frame.

On top of this set-up, implementation of the data store interface is
straightforward. Note that during the `equal` operation a set of variables pairs
that are compared during the notsubsetq operation needs to be computed, as the
segments mapping is not canonical and we cannot directly compare variables from
the same segment number in different states.

This naive implementation does not scale well, as path condition grows quickly
(\llvm bit-code uses a considerable number of registers, because \llvm is a
static single assignment language) and an enormous number of expensive
quantified \smt queries is performed. Thus, \smt store uses the following
optimizations:

* Unused variable definitions -- the path condition is split into two parts:
  list of definitions in the form $variable = expression$, and a list of path
  condition clauses in the form of $variable \operatorname{rel_{op}}
  variable$\footnote{a constant can also figure in such a clause}. Definitions
  are mainly collected during arithmetic, `store` and `load` instructions. Path
  condition contains only constraints collected during the `prune` operation.
  This severance to two independent pieces allows us to easily remove unused
  definitions without a complicated analysis when the function returns. The
  return value can be easily expressed through simple syntactic substitution
  using only function parameters and all variables from the function segment can
  be removed from the definitions and the path condition clauses. When a formula
  is needed, a simple conjunction of all definitions and path condition clauses
  is constructed. This optimization significantly reduces the size of path
  condition (and thus the size of \smt queries to a solver) and also keeps the
  set of program segments small.

* Syntactical equivalence checking -- as \symdivine aims for verification of
  parallel programs, the same path conditions due to diamond-shapes in the
  multi-state can be produced. As \smt query to a solver is expensive operation
  even for simple queries \cite{Havel2014thesis}, \symdivine tries to perform
  simple syntactic equality test of path conditions before executing this query.
  Non-trivial number of solver calls can be saved in this way.

* Simplification -- Z3 \smt solver offers several simplification strategies that
  can be applied to a path condition. These strategies can be applied to a path
  condition in order to produce smaller or easier forms of equivalent path
  condition. Simplification is applied when a new formula with a large number of
  variables is produced.

\begin{figure}[!ht]
\begin{center}
\resizebox{0.8\textwidth}{!}{
    \begin{tikzpicture}[ ->, >=stealth', shorten >=1pt, auto, node distance=1.5cm
                       , semithick
                       , scale=0.7
                       , font=\sffamily
                       , seg/.style = {
                            rectangle,
                            draw,
                            minimum width = 3em,
                            minimum height = 2em,
                            fill=gray!60!white},
                       , gen/.style = {
                            rectangle,
                            draw,
                            minimum width = 2em,
                            minimum height = 2em},
                       , thread/.style = {
                            rectangle,
                            draw,
                            minimum width = 5em,
                            minimum height = 1.2em},
                       ]

    \node[seg, fill=white] (seg0) {segments};
    \foreach \x [evaluate=\x as \prev using \x-1] in {1,...,8}  {
        \node[seg, right = 0pt of seg\prev] (seg\x) {\x};
    }

    \pgfmathsetseed{1138}

    \foreach \x in {1,...,8} {
        \pgfmathsetmacro{\vars}{int(random(5))}

        \pgfmathsetmacro{\geni}{int(random(0,4))}
        \node[gen, below = 1em of seg\x] (gen\x 1) {g\geni};
        \path[->] (seg\x) edge (gen\x 1);
        \foreach \prev [evaluate=\prev as \y using int(\prev+1)] in {1,...,\vars} {
            \pgfmathsetmacro{\gen}{int(random(0,4))}
            \node[gen, below = 0 cm of gen\x\prev] (gen\x\y) {g\gen};
        }        
    }

    \node[thread, fill=gray!60!white, above = 9 em of seg1] (t10) {Thread 1};
    \node[thread, below = 0pt of t10] (t11) {foo1};
    \node[thread, below = 0pt of t11] (t12) {foo2};

    \node[thread, fill=gray!60!white, above = 9 em of seg4] (t20) {Thread 2};
    \node[thread, below = 0pt of t20] (t21) {foo2};
    \node[thread, below = 0pt of t21] (t22) {foo2};
    \node[thread, below = 0pt of t22] (t23) {foo3};
    \node[thread, below = 0pt of t23] (t24) {foo2};

    \node[thread, fill=gray!60!white, above = 9 em of seg7] (t30) {Thread 3};
    \node[thread, below = 0pt of t30] (t31) {foo3};
    \node[thread, below = 0pt of t31] (t32) {foo4};

    \path[->]
        (t12.south) edge [in = 90, out = 270] (seg4.north)
        (t11.west) edge [in = 90, out = 180] (seg1.north)
        (t21.west) edge [in = 90, out = 180] (seg2.north)
        (t22.west) edge [in = 90, out = 180] (seg3.north)
        (t23.east) edge [in = 90, out = 0] (seg6.north)
        (t24.east) edge [in = 90, out = 0] (seg7.north)
        (t31.west) edge [in = 90, out = 180] (seg5.north)
        (t32.south) edge [in = 90, out = 270] (seg8.north)
        ;

    \end{tikzpicture}
    }
    \caption{Illustration of path condition meta information organisation in
    \smt store. Each thread has its own call stack. When a function is
    called, \texttt{add\_segment} is called on the \smt store and a new segment
    is created. Each segment points to a list of variables in the given segment
    that keeps track of currently-highest generation of each variable as shown
    in the picture. Note that the mapping call stack frames to a segment is not
    canonical and, depending on thread interleaving, it may vary.}
    \label{fig:mapping}
\end{center}
\end{figure}
