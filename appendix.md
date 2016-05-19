# Archive Structure

The archive submitted with this thesis contains a snapshot of the git repository\footnote{\url{https://github.com/yaqwsx/SymDivine}} with
\symdivine source code and sources of the thesis itself with all the
measurements we have used to evaluate dependency-based caching.

The repository maps whole development of \symdivine during writing of this
thesis including re-implementation of \ltl algorithm, extension of \llvm
interpreter to support two new instructions, implementation of naive caching,
implementation of dependency-based caching and several bug-fixes and small
improvements of the tool.

# Running \symdivine

\symdivine can be either compiled from source or obtained in binary form repository
release page\footnote{\url{https://github.com/yaqwsx/SymDIVINE/releases}}.
Runtime dependencies of \symdivine are Z3 and ltl2tgb, libboost-graph1.54.0,
gcc-4.9 (or higher) and g++-4.9 (or higher).

To compile \symdivine, following dependencies has to be installed on the target
system: CMake 2.8 (or higher), make, llvm-3.4, boost, flex and bison. \symdivine then can be compiled by:
```{.bash}
./configure
cd build
make
```
Final binary file is located in the `bin` directory. \symdivine then can be run using following commands (first one runs reachability algorithm, the second one run \ltl algorithm):

```{.bash}
bin/symdivine reachability <model.ll> [options]
bin/symdivine ltl <property> <model.ll> [options]
```
See `bin/symdivne help` for more info. It is also possible to use helper
script `scripts/run_symdivine.py`, which takes a C a C++ file, compiles it and
runs SymDIVINE, to easily start verification of a C or C++ benchmark.

