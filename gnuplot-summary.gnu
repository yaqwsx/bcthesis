set style line 2 lc rgb '#003999' lt 2 lw 3
set style line 1 lc rgb '#FF9933' lt 2 lw 3
set format y "%.0f"
set format y "%.0f"
set xlabel "Time with SMT store [s]"
set ylabel "Time with Partial store [s]"
set yrange [0.01:400]
set xrange [0.01:400]
unset key

f(x) = x

set style line 12 lc rgb '#808080' lt 0 lw 1
set grid back ls 12

set terminal epslatex size 13cm,12cm color colortext
set output output_file

plot input_file with points pointtype 2 lc rgb '#ff9933', f(x) with lines ls 2
