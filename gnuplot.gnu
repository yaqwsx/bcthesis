set style line 2 lc rgb '#003999' lt 2 lw 2.5
set style line 1 lc rgb '#FF9933' lt 2 lw 2.5
set format y "%.0f"
set xlabel "Benchmark count"
set ylabel "Time [s]"
# set yrange [0:240]
set key left top
#set xtics 5
#set ytics 10
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid back ls 12

set terminal epslatex size 13cm,8.65cm color colortext
set output output_file


plot input_dir."/_no_cache_plot.txt" with lines ls 1 title "No cache", input_dir."/_cache_plot.txt" with lines ls 2 title "With cache"