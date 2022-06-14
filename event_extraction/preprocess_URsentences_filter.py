import csv
with open('data.tsv','r') as fin,open('user_rights_sentences.tsv','w') as fout:
    reader = csv.reader(fin,delimiter='\t')
    writer = csv.writer(fout,delimiter='\t')
    #writer.writerow(["label", "review", "filename"])
    #writer.writeheader()
    for row in reader:
        if row[0] == '10' or row[0] == '9' or row[0] == '8' or row[0] == '7' or row[0] == '6' or row[0] == '5':
            writer.writerow(row)
