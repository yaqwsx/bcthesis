# Bachelor's thesis: Caching SMT Queries in SymDivine

*author: Jan Mrázek*

*advisor: doc. RNDr. Jiří Barnat, Ph.D.*

## Abstract

Scalability of automatic verification tools is a crucial factor for usability of such tools in practise. There are vast number of ways to improve it. Trading off space for time is one of a classic approaches to improving time efficiency of these tools, mainly used when constraints satisfiability checking plays a central role. Caching of quantifier-free Satisfiability Modulo Theories (SMT) queries is now widely used in the world of symbolic execution. SymDIVINE is a tool for bit-precise control-explicit data-symbolic model checking of parallel C and C++ programs. Quantified SMT queries for multi-state equality decisions play a central role in SymDIVINE and take most of the verification time. Standard caching techniques do not work due to the quantification. In this thesis we propose dependency-based caching for quantified SMT queries, that are used in SymDIVINE. We also demonstrate integration of it in SymDIVINE and provide experimental evaluation on a diverse set of benchmarks.

Full text can be found [here on GitHub](thesis.pdf) or via [IS MUNI archive](https://is.muni.cz/th/422279/fi_b/?lang=en).

