set style line 2 lc rgb '#003999' lt 17 lw 2.5
set style line 1 lc rgb '#FF9933' lt 19 lw 2.5
set format y "%.0f"
set xlabel "Benchmarks solved"
set ylabel "Timeout [s]"
# set yrange [0:240]
set key left top
#set xtics 5
#set ytics 10
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid back ls 12

set terminal epslatex size 13cm,8cm color colortext
set output output_file


plot input_dir."/_no_cache_plot.txt" with lines ls 1 title "SMT store", "" with points pointtype 5 lc rgb '#ff9933' notitle, input_dir."/_cache_plot.txt" with lines ls 2 title "Partial store", "" with points pointtype 4 lc rgb '#003999' notitle