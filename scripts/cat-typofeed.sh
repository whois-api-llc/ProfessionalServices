# Example of how to read the typo-squatting data feed provided by WHOISXMLAPI.COM
# ed@whoisxmlapi.com
#
line=0
INPUT=data.csv
IFS=','
echo "File name = $INPUT"
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
while read group_number group_member_number total_no_of_group_members domain domain_utf
do
   ((line++))
   if [[ $line -eq 1 ]]; then
      continue;
   fi
   echo "$group_number,$group_member_number,$total_no_of_group_members,$domain"
done < $INPUT
echo "Total lines: $line"
