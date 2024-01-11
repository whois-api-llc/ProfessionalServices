import csv
import sys

def read_csv_with_multiline(input_file, output_file, email_file, tld):

    ofile = open(output_file, "w", newline='', encoding='utf-8')
    csv_owriter = csv.writer(ofile)

    efile = open(email_file, "w", newline='', encoding='utf-8')
    csv_ewriter = csv.writer(efile)

    with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.reader(csvfile)

        for row in csv_reader:
            new_row = [cell.replace('\n', '|') if '\n' in cell else cell for cell in row]
            csv_owriter.writerow(new_row)

            email_list = new_row[3].split('|')

            for e in email_list:
                if len(e) > 6:
                    if e.endswith(tld):
                        email_row = [new_row[1], e]
                        csv_ewriter.writerow(email_row)

read_csv_with_multiline(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
