import pandas as pd

df1= pd.read_csv('Fragrantica_dataset.csv')
df2 = pd.read_csv('Ajout_Fragrantica_dataset.csv')
print(df1.shape)
print(df2.shape)
combined_df = pd.concat([df1, df2], axis=0)
combined_df = combined_df.drop_duplicates(subset=['url'], keep='first')
print(combined_df.shape)
combined_df.to_csv('Fragrantica_Dataset.csv', index=False)


