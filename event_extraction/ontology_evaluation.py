# evaluation
import csv
with open('./output/data_10_ground_truth.tsv', 'r') as source, open('./output/user_rights_data_10_result.tsv', 'r') as tested:
    source_r = csv.reader(source,delimiter='\t')
    tested_r = csv.reader(tested,delimiter='\t')
    TP_accessNouns = 0
    TP_FP_accessNouns = 0
    TP_FN_accessNouns = 0
    counter = 0
    for row_s, row_t in zip(source_r, tested_r):
        if counter > 50:
            break
        else:
            counter += 1
        if row_s[0] == 'sentence':
            print('skip header')
            continue

        if row_s[6] != 'NaN':
            TP_FN_accessNouns += 1
        if row_t[4] != 'NaN':
            TP_FP_accessNouns += 1

        if row_s[6] != 'NaN' and row_t[4] == 'NaN':
            print('TN missing sentence with accessNouns: ', row_s[0], row_s[6], row_t[4])
        if row_s[6] == 'NaN' and row_t[4] != 'NaN':
            print('FP non-targeted sentence predicted: ', row_s[0], row_s[6], row_t[4])

        if row_s[6] != 'NaN' and row_t[4] != 'NaN':
            print(row_s[6],row_t[4])
            if row_s[6] in row_t[4]: # to add type if sting, then in; if list then loop or any
                TP_accessNouns += 1
                print(row_s[6],row_t[4])
            else:
                print('wrong predicted sentence with accessNouns: ', row_s[0], row_s[6], row_t[4])

    print('TP_accessNouns: ', TP_accessNouns)
    print('TP_FP_accessNouns: ', TP_FP_accessNouns) # trigger word
    print('TP_FN_accessNouns: ', TP_FN_accessNouns)
    print('precision_accessNouns: ', TP_accessNouns/TP_FP_accessNouns)
    print('recall_accessNouns: ', TP_accessNouns/TP_FN_accessNouns)

# TP_accessNouns:  6
# TP_FP_accessNouns:  6
# TP_FN_accessNouns:  9
# precision_accessNouns:  1.0
# recall_accessNouns:  0.6666666666666666