#!/bin/bash

filename="$1"

base_name=$(basename -s .csv "$filename")

csvgrep -c 1 -m "added" "$filename" > "$base_name.added.csv"

csvgrep -c 1 -m "dropped" "$filename" > "$base_name.dropped.csv"

csvgrep -c 1 -m "updated" "$filename" > "$base_name.updated.csv"

csvgrep -c 1 -m "discovered" "$filename" > "$base_name.discovered.csv"

#
# The NRD2.0 CSVs may contain newline characters in the rawText field, which are valid CSVs, and newlines in quoted records are allowed by the CSV standards.
#
# However, it is not always easy to parse them in this case. So we can recommend using any CSV parser, for example, from the csvkit package. You can filter out rows by 1st column value, for example:
# csvgrep -c 1 -m "added" ./nrd.2021-11-25.ultimate.daily.data.csv
# The above bash script may help do it for all types of records.
#
# As a workaround, you can remove the annoying newlines (CR/LF) by using, for example, the following command in the Linux shell environment:
#
# awk '(NR-1)%2{$1=$1}1' RS=\" ORS=\" ./nrd.2021-11-25.ultimate.daily.data.csv
# In this case, the rawText data will no longer be raw.
#
