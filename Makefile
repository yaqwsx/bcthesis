ALL=$(wildcard *.md)

all : thesis.pdf archive_README.pdf

clean:
	rm -f *.aux *.bbl *.bcf *.blg *.log *.out *.pyg *.run.xml *.toc
	rm -f appendix.tex caching.tex conclusion.tex intro.tex preliminaries.tex \
		results.tex symdivine.tex README.tex
	rm -f *chart.tex *chart.eps *eps-converted-to.pdf summary.txt

thesis.pdf : thesis.tex results $(ALL:.md=.tex) thesis.bbl
	bash ./latexwrap $<

thesis-print.pdf : thesis-print.tex $(ALL:.md=.tex) thesis-print.bbl thesis.lua
	bash ./latexwrap $<

thesis-print.tex : thesis.tex
	sed -e 's/linkcolor={.*}/linkcolor={black}/' \
		-e 's/citecolor={.*}/citecolor={black}/' \
		-e 's/urlcolor={.*}/urlcolor={black}/' \
		-e 's/\\iffalse.*%@ifprint/\\iftrue/' \
		$< > $@

%.bbl : bibliography.bib %.bcf
	-biber $(@:.bbl=)

%.bcf :
	bash ./latexwrap -n1 $(@:.bcf=.tex)

results:
	cd results/vojta/bitvector; ../../../process_results.py no_cache_no_flags.csv cache_partial_store_dontsimplify.csv
	cd results/vojta/eca; ../../../process_results.py no_cache_no_flags.csv cache_partial_store_dontsimplify.csv
	cd results/vojta/locks; ../../../process_results.py no_cache_no_flags.csv cache_partial_store_dontsimplify.csv
	cd results/vojta/loops; ../../../process_results.py no_cache_no_flags.csv cache_partial_store_dontsimplify.csv
	cd results/vojta/recursive; ../../../process_results.py no_cache_no_flags.csv cache_partial_store_dontsimplify.csv
	cd results/vojta/ssh-simplified; ../../../process_results.py no_cache_no_flags.csv cache_partial_store_dontsimplify.csv
	cd results/vojta/systemc; ../../../process_results.py no_cache_no_flags.csv cache_partial_store_dontsimplify.csv
	cd results/concurrency; ../../process_results.py no_cache_no_flags.csv cache_partial_store_dontsimplify.csv
	cd results/ltl; ../../process_results.py no_cache_no_flags.csv cache_partial_store_dontsimplify.csv
	gnuplot -e "output_file='bitvector_chart.tex'" -e "input_dir='results/vojta/bitvector'" gnuplot.gnu
	gnuplot -e "output_file='eca_chart.tex'" -e "input_dir='results/vojta/eca'" gnuplot.gnu
	gnuplot -e "output_file='locks_chart.tex'" -e "input_dir='results/vojta/locks'" gnuplot.gnu
	gnuplot -e "output_file='loops_chart.tex'" -e "input_dir='results/vojta/loops'" gnuplot.gnu
	gnuplot -e "output_file='recursive_chart.tex'" -e "input_dir='results/vojta/recursive'" gnuplot.gnu
	gnuplot -e "output_file='ssh_chart.tex'" -e "input_dir='results/vojta/ssh-simplified'" gnuplot.gnu
	gnuplot -e "output_file='systemc_chart.tex'" -e "input_dir='results/vojta/systemc'" gnuplot.gnu
	gnuplot -e "output_file='concur_chart.tex'" -e "input_dir='results/concurrency'" gnuplot.gnu
	gnuplot -e "output_file='ltl_chart.tex'" -e "input_dir='results/ltl'" gnuplot.gnu
	./process_summary_results.py summary.txt results/vojta/bitvector \
		results/vojta/eca \
		results/vojta/loops \
		results/vojta/locks \
		results/vojta/recursive \
		results/vojta/ssh-simplified \
		results/vojta/systemc \
		results/concurrency \
		results/ltl
	gnuplot -e "output_file='summary_chart.tex'" -e "input_file='summary.txt'" gnuplot-summary.gnu 

.PRECIOUS: %.bcf %.bbl

%.tex : %.md
	pandoc $< -o $@
	sed -i $@ -re 's/ \\cite/~\\cite/' \
		-e 's/^\\section\{@FIG:([^\}]*)\}.*$$/\\begin{figure}[\1]/' \
		-e 's/^\\section\{@eFIG\}.*$$/\\end{figure}/' \
		-e 's/\\begCaption/\\caption{/' -e 's/\\endCaption/\}/' \
		-e 's/\\begFigure/\\begin{figure}/' -e 's/\\endFigure/\\end{figure}/' \
		-e 's/\\begSplit/\\begin{minipage}[t]{0.48\\textwidth}/' \
		-e 's/\\Split/\\end{minipage}\\hfill\\begin{minipage}[t]{0.48\\textwidth}/' \
		-e 's/\\endSplit/\\end{minipage}/' \
		-e 's/\\texorpdfstring\{\\llvm\}\{\}/\\texorpdfstring\{\\llvm\}\{LLVM\}/' \
		-e 's/\{Interpreter \}/\{LLVM Interpreter \}/'
	vlna -l -m -n $@

watch :
	while true; do inotifywait -e close_write,moved_to,create .; sleep 1; make; done

.PHONY: watch

txt: $(ALL:.md=.txt)

.PHONY: txt results

%.txt : %.md
	sed -e ':a;N;$$!ba;s/\n\n/@NL@/g' $< | \
		sed -e ':a;N;$$!ba;s/\n/ /g' -e 's/@NL@/\n\n/g' \
			-e 's/\\autoref{[^}]*}//g' -e 's/\\//g' > $@