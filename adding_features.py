import pandas as pd
import numpy as np

# 1. Load the enriched dataset
print("Loading data...")
df = pd.read_csv('final_movies_dataset_enriched_full.csv', low_memory=False)

# --- Step A: Calculate Rating Statistics (Per Movie) ---
print("Calculating rating statistics (Count, Mean, Std)...")

# We group by Title and Release_Year to ensure we treat each movie individually
# 'rating' is the column we are analyzing
movie_stats = df.groupby(['Title', 'Release_Year'])['rating'].agg(
    Rating_Count='count',      # Popularity
    Avg_Rating='mean',         # Quality
    Controversy_Score='std'    # Controversy (Standard Deviation)
).reset_index()

# Handle cases where std is NaN (movies with only 1 rating have no deviation)
movie_stats['Controversy_Score'] = movie_stats['Controversy_Score'].fillna(0)

# Merge these new stats back into the main dataframe
# This adds the 3 new columns to every row based on the movie
df = pd.merge(df, movie_stats, on=['Title', 'Release_Year'], how='left')

# --- Step B: Calculate ROI (Financial Success) ---
print("Calculating ROI...")

# Ensure budget and revenue are numeric
df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce')

# Calculate ROI: (Revenue - Budget) / Budget
# We use np.where to avoid DivisionByZero errors if budget is 0 or NaN
# Logic: If budget > 1000 (filtering out tiny/error budgets) AND revenue exists -> Calculate. Else -> NaN.
valid_budget = (df['budget'] > 1000) & (df['revenue'].notna())

df['ROI'] = np.where(
    valid_budget,
    (df['revenue'] - df['budget']) / df['budget'],
    np.nan
)

# --- Step C: Create 'Decade' column (Bonus for visualizations) ---
# This is very useful for the visualizations we discussed (Ridgeline plots etc.)
df['Decade'] = (df['Release_Year'] // 10) * 10

# --- Save Final File ---
output_filename = 'final_project_data_ready.csv'
df.to_csv(output_filename, index=False)

print("-" * 30)
print(f"Process complete. Saved to: {output_filename}")
print("New columns added: 'Rating_Count', 'Avg_Rating', 'Controversy_Score', 'ROI', 'Decade'")
print("\nSample Data (First 5 rows with new columns):")
print(df[['Title', 'rating', 'Avg_Rating', 'Controversy_Score', 'ROI']].head(5).to_string())