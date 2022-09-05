import csv

def write_row(row, number):
    with open('./input/user_rights_data_' + str(number) + '_sentences.tsv','a') as fout:
        writer = csv.writer(fout, delimiter='\t')
        writer.writerow(row)

with open('./input/data.tsv','r') as fin:
    reader = csv.reader(fin, delimiter='\t')
    #writer.writerow(["label", "review", "filename"])
    #writer.writeheader()
    for row in reader:
        if row[0] == '10':
            write_row(row, '10')
        elif row[0] == '9':
            write_row(row,'9')
        elif row[0] == '8':
            write_row(row, '8')
        elif row[0] == '7':
            write_row(row, '7')
        elif row[0] == '6':
            write_row(row,'6')
        elif row[0] == '5':
            write_row(row, '5')