
import pandas as pd

filepath = './output_before_dedup/user_rights_data_5_single_keywords.tsv'
df = pd.read_csv(filepath,sep='\t')
noun_dict = dict(zip(df['NOUN'], df['NOUN_weight']))
sorted_noun_dict = dict(sorted(noun_dict.items(), key=lambda item: item[1],reverse=True))
# print(dict(list(sorted_noun_dict.items())[0:5]))
df_nouns = pd.DataFrame(sorted_noun_dict.items(), columns=['NOUN', 'NOUN_weight'])
print(df_nouns.head())

propn_dict = dict(zip(df['PROPN'], df['PROPN_weight']))
sorted_propn_dict = dict(sorted(propn_dict.items(), key=lambda item: item[1],reverse=True))
# print(dict(list(sorted_noun_dict.items())[0:5]))
df_propns = pd.DataFrame(sorted_propn_dict.items(), columns=['PROPN', 'PROPN_weight'])
print(df_propns.head())

verb_dict = dict(zip(df['VERB'], df['VERB_weight']))
sorted_verb_dict = dict(sorted(verb_dict.items(), key=lambda item: item[1],reverse=True))
# print(dict(list(sorted_noun_dict.items())[0:5]))
df_verbs = pd.DataFrame(sorted_verb_dict.items(), columns=['VERB', 'VERB_weight'])
print(df_verbs.head())

keybert_dict = dict(zip(df['KeyBert'], df['KeyBert_weight']))
sorted_keybert_dict = dict(sorted(keybert_dict.items(), key=lambda item: item[1],reverse=True))
# print(dict(list(sorted_noun_dict.items())[0:5]))
df_keybert = pd.DataFrame(sorted_keybert_dict.items(), columns=['KeyBert', 'KeyBert_weight'])
print(df_keybert.head())

df_all = pd.concat([df_nouns,df_propns, df_verbs, df_keybert],axis=1)
print(df_all.head())

output_filename = './output_before_dedup/'+'sorted_'+str(filepath).split('/')[-1].split('.')[0]+'.tsv'
df_all.to_csv(output_filename, sep='\t', encoding='utf-8', index=False)
