import pandas as pd

df_all = pd.read_csv('All_Fragrantica_dataset.csv')
df = pd.read_csv('Fragrantica_dataset_Hichem.csv')
print(df_all.shape)
print(df.shape)
combined_df = pd.concat([df_all, df], axis=0)
combined_df = combined_df.drop_duplicates(subset=['nom_parfum', 'marque', 'launch_year', 'url'], keep='first')
print(combined_df.shape)
combined_df.to_csv('All_Fragrantica_Dataset.csv', index=False)


