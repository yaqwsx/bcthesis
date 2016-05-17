In this chapter we present experimental evaluation of our dependency-based
caching a we discuss strengths and weaknesses of our approaches.

# Reachability benchmarks

We have taken a subset of C benchmarks from SV-COMP \cite{SVCOMP} benchmark
suite. Benchmarks from following subdirectories were taken: bitvector, eca,
locks, loops, recursive, ssh-simplified, systemc, pthread, pthread-atomic,
pthread-ext, pthread-lit and pthread-wmm. We ran \symdivine without caching on a
machine with Intel Core i5-4690 CPU (3.50\ GHz) and 16\ GB of RAM. Each
benchmark was compiled with three different level of optimizations into \llvm
bit-code -- `-O0`, `-Os` and `-O2`. All benchmarks run with time-out 4 minutes.
We ran \symdivine with original \smt store and multiple different configurations
using \smt partial store, which implements dependency-based caching.

We also verified correctness of implementation of partial \smt store. We
implemented so-called *validity test* in partial \smt store. This validity test
keeps 2 multi-states -- one represented by \smt store and the other one by
partial \smt store. All multi-state manipulations are performed simultaneously
on both stores. When an empty or an equal operation is performed, results of
partial \smt store are tested against \smt store. The results has to match. We
ran all benchmarks mentioned above using this test and not a single mismatch
occurred.

# \ltl benchmarks

We have taken C LTL benchmarks that have been used in \cite{BHB14} for
benchmarking of first \ltl implementation in \symdivine. Then we followed
similar methodology as during benchmarking reachability. For every benchmark, 3
different \llvm bit-codes with different levels of optimizations were produced.
Then we ran \symdivine with timeout 4 minutes. We have tested validity of given
property for each benchmark and its negation. Comparison of results can be seen
Todo


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
\end{longtable}

\begin{figure}
    \input{bitvector_chart.tex}
    \caption{Bitvector set}
\end{figure}

\begin{figure}
    \input{eca_chart.tex}
    \caption{Eca set}
\end{figure}

\begin{figure}
    \input{locks_chart.tex}
    \caption{Locks set}
\end{figure}

\begin{figure}
    \input{loops_chart.tex}
    \caption{Loops set}
\end{figure}

\begin{figure}
    \input{recursive_chart.tex}
    \caption{Recursive set}
\end{figure}

\begin{figure}
    \input{ssh_chart.tex}
    \caption{SSH-simplified set}
\end{figure}

\begin{figure}
    \input{systemc_chart.tex}
    \caption{SystemC set}
\end{figure}

\begin{figure}
    \input{concur_chart.tex}
    \caption{Concurrency set}
\end{figure}

\begin{figure}
    \input{summary_chart.tex}
    \caption{Overall summary}
\end{figure}