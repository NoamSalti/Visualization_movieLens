import pandas as pd
import re

# ============================================================
#  Goal:
#  Enrich the main movies dataset with metadata fields (revenue, budget, etc.)
#  by matching movies between two CSV files using a cleaned "join_key" + closest year.
# ============================================================

# # --- Helper functions for cleaning/matching ---
# def get_clean_join_key(text):
#     # Create a normalized key from a movie title for robust matching
#     if not isinstance(text, str):
#         return ""
#     text = text.replace('&', 'and')             # Replace '&' with 'and'
#     text = re.sub(r'\([^)]*\)', '', text)       # Remove parentheses and their content
#     text = text.lower()                         # Lowercase
#     text = re.sub(r'[^a-z0-9\s]', '', text)     # Keep only letters, numbers, and spaces
#     words = text.split()
#     words.sort()                                # Sort words to reduce ordering issues
#     return " ".join(words)
#
# def calculate_diff(row):
#     # Compute absolute year difference to pick the closest match
#     if pd.isna(row['year_meta']) or pd.isna(row['revenue']):
#         return 9999
#     return abs(row['year_main'] - row['year_meta'])
#
# # --- 1. Load data ---
# print("Loading data...")
# main_df = pd.read_csv('final_movies_dataset.csv', low_memory=False)
# meta_df = pd.read_csv('movies_metadata.csv', low_memory=False)
#
# # Strip column name whitespace to avoid subtle merge/key issues
# main_df.columns = main_df.columns.str.strip()
#
# # --- 2. Build unique movie list (avoid working on the full huge table first) ---
# print("Creating unique movies list for matching...")
# unique_movies = main_df[['Title', 'Release_Year']].drop_duplicates().copy()
#
# # Prepare join keys + numeric year in the main dataset
# unique_movies['join_key'] = unique_movies['Title'].apply(get_clean_join_key)
# unique_movies['year_main'] = pd.to_numeric(unique_movies['Release_Year'], errors='coerce').fillna(0).astype(int)
#
# # --- 3. Prepare metadata ---
# print("Preparing metadata...")
# meta_df['release_date'] = pd.to_datetime(meta_df['release_date'], errors='coerce')
# meta_df['year_meta'] = meta_df['release_date'].dt.year.fillna(0).astype(int)
# meta_df['join_key'] = meta_df['title'].apply(get_clean_join_key)
#
# # Keep only the columns we want to attach to the final dataset
# cols_to_keep = ['join_key', 'year_meta', 'revenue', 'budget', 'overview', 'poster_path', 'runtime', 'original_language']
# meta_subset = meta_df[cols_to_keep].copy()
#
# # Drop duplicates inside metadata to reduce memory usage during merge
# meta_subset = meta_subset.drop_duplicates(subset=['join_key', 'year_meta'])
#
# # --- 4. Find best match per movie (closest year among same-title candidates) ---
# print("Matching metadata to unique movies...")
#
# # Merge by join_key first (may create multiple candidate matches per movie)
# candidates = pd.merge(unique_movies, meta_subset, on='join_key', how='left')
#
# # Compute year difference for each candidate
# candidates['year_diff'] = candidates.apply(calculate_diff, axis=1)
#
# # Sort so that the best match becomes the first row per (Title, Release_Year)
# candidates.sort_values(by=['Title', 'Release_Year', 'year_diff'], ascending=[True, True, True], inplace=True)
#
# # Keep only the best match per movie
# best_matches = candidates.drop_duplicates(subset=['Title', 'Release_Year'], keep='first')
#
# # Remove helper columns before the final merge back into the full dataset
# cols_to_drop = ['join_key', 'year_main', 'year_meta', 'year_diff']
# best_matches = best_matches.drop(columns=cols_to_drop)
#
# # --- 5. Final merge back into the original full dataset ---
# print("Applying matched data back to original full dataset...")
# final_df = pd.merge(main_df, best_matches, on=['Title', 'Release_Year'], how='left')
#
# # --- 6. Save + basic validation ---
# output_filename = 'final_movies_dataset_enriched_full.csv'
# final_df.to_csv(output_filename, index=False)
#
# print("-" * 30)
# print(f"Process complete.")
# print(f"Original Rows: {len(main_df)}")
# print(f"Final Rows:    {len(final_df)} (Must be equal!)")
# print(f"Rows with Revenue: {final_df['revenue'].notna().sum()}")
#
# # Quick sanity check on a known title (should appear multiple times if there are many ratings rows)
# print("\nDebug Check (Granularity):")
# sample_movie = 'Swimming with Sharks'
# sample_rows = final_df[final_df['Title'].str.contains(sample_movie, na=False, case=False)]
# print(f"Movie: {sample_movie}")
# print(f"Number of rating rows found: {len(sample_rows)} (Should be > 1)")
# if not sample_rows.empty:
#     print(f"Revenue attached: {sample_rows['revenue'].iloc[0]}")

# Load the enriched output and preview the first 50 rows
data = pd.read_csv('final_movies_dataset_enriched_full.csv')
print(data.head(50).to_string())