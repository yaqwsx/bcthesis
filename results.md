In this chapter we present an experimental evaluation of our dependency-based
caching a we discuss strengths and weaknessbes of our approaches. We have
evaluated both algorithms (reachability and \ltl) from current version of
\symdivine with dependency-based caching.

# Benchmark set

To evaluate reachability, we have taken a subset of C benchmarks from SV-COMP
\cite{SVCOMP} benchmark suite. Benchmarks from following subdirectories were
taken: bitvector, eca, locks, loops, recursive, ssh-simplified, systemc,
pthread, pthread-atomic, pthread-ext, pthread-lit and pthread-wmm. To evaluate
\ltl algorithm, we have used \ltl benchmarks, which have been used in
\cite{BHB14} for benchmarking of first \ltl implementation in \symdivine. We ran
\symdivine with caching on a machine with Intel Core i5-4690 CPU (3.50\ GHz)
and 16\ GB of RAM. Each benchmark was compiled with three different level of
optimizations into \llvm bit-code -- `-O0`, `-Os` and `-O2`. \ltl benchmarks
were tested for their specification and its negation. All benchmarks ran with
time-out 4 minutes. Then we have run the same set of benchmarks without caching
using the original implementation of \smt Store and no time-out. The time-out
was disabled in order to see improvements caused by caching, as many benchmarks
without caching time-outed and no relevant data cannot be obtained. Also we
excluded simple benchmarks with no equal queries as they are not relevant to
caching.

We also verified correctness of implementation of partial \smt store. We
implemented so-called *validity test* in partial \smt store. This validity test
keeps 2 multi-states -- one represented by \smt store and the other one by
partial \smt store. All multi-state manipulations are performed simultaneously
on both stores. When an empty or an equal operation is performed, results of
partial \smt store are tested against \smt store. The results has to match. We
ran all benchmarks mentioned above using this test and not a single mismatch
occurred.

# Evaluation

We had several expectations about results. We expected 

- **bitvector** --

- **eca** --

- **locks** --

- **loops** --

- **recursive** --

- **ssh-simplified** --

- **system-c** --

- **concurrency** --

- \textbf{\ltl} --

\begin{longtable}{l@{\hskip 0.1cm}rrrrrrrR{1.7bbbbbcm}}  
    \caption{Summary results showing effects of caching}\label{tab:summary}\\   
    \mcrot{1}{l}{60}{\pbox{20cm}{Category  \\ name}} & \mcrot{1}{l}{60}{\pbox{20cm}{Time without \\ caching [s]}} & \mcrot{1}{l}{60}{\pbox{20cm}{Time with \\ caching [s]}} & \mcrot{1}{l}{60}{\pbox{20cm}{Percentage \\ difference}} & \mcrot{1}{l}{60}{Equal queries} & \mcrot{1}{l}{60}{\pbox{20cm}{Solver calls \\ without cache}} & \mcrot{1}{l}{60}{\pbox{20cm}{Solver calls \\ with cache}} \\ \toprule
    bitvector      & $3619.5$ & $2531.5$ & \SI{-30.1}{\percent} & $16570$   & 165470 & $6854$ \\ \midrule
    eca            & $488.9$  & $696.1$  & \SI{42.4}{\percent}  & $18695$   & 18695 & $5173$ \\ \midrule
    locks          & $243.9$  & $237.0$  & \SI{-2.8}{\percent}  & $2040$    & 2040 & $377$  \\ \midrule
    loops          & $81.5$   & $58.3$   & \SI{-28.4}{\percent} & $5755$    & 5745 & $4113$ \\ \midrule
    recursive      & $16.0$   & $16.6$   & \SI{4.0}{\percent}   & $372$     & 372 & $109$  \\ \midrule
    ssh-simplified & $4557.9$ & $3069.5$ & \SI{-32.7}{\percent} & $238280$  & 238280 & $571$  \\ \midrule
    system-c       & $3338.6$ & $1920.9$ & \SI{-42.5}{\percent} & $225906$  & $225906$ & $43513$\\ \midrule
    concurrency    & $943.0$  & $494.6$  & \SI{-47.6}{\percent} & $1769313$ & 96214 & $9619$ \\ \bottomrule
    \textbf{summary} & $13289.3$ & $9024.5$ & \SI{-32.0}{\percent} & $2276931$ & $752722$ & $70329$ \\ \bottomrule
\end{longtable} 

\begin{figure}
    \input{bitvector_chart.tex}
    \caption{Bitvector set}
    \label{fig:bitvector_set}
\end{figure}

\begin{figure}
    \input{eca_chart.tex}
    \caption{Eca set}
    \label{fig:eca_set}
\end{figure}

\begin{figure}
    \input{locks_chart.tex}
    \caption{Locks set}
    \label{fig:locks_set}
\end{figure}

\begin{figure}
    \input{loops_chart.tex}
    \caption{Loops set}
    \label{fig:loops_set}
\end{figure}

\begin{figure}
    \input{recursive_chart.tex}
    \caption{Recursive set}
    \label{fig:recursive_set}
\end{figure}

\begin{figure}
    \input{ssh_chart.tex}
    \caption{SSH-simplified set}
    \label{fig:ssh_set}
\end{figure}

\begin{figure}
    \input{systemc_chart.tex}
    \caption{SystemC set}
    \label{fig:systemc_set}
\end{figure}

\begin{figure}
    \input{concur_chart.tex}
    \caption{Concurrency set}
    \label{fig:concurrency_set}
\end{figure}

\begin{figure}
    \input{summary_chart.tex}
    \caption{Overall summary}
    \label{fig:overall_set}
\end{figure}