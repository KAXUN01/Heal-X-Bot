import os
import sys

# Ensure the model directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from train_xgboost_model import DataLoader

def main():
    print("Generating synthetic predictive maintenance dataset...")
    
    # Initialize the data loader
    loader = DataLoader(prediction_horizon=[1, 6, 24])
    
    # Generate 15000 samples to make it look substantial and realistic
    # This represents about 10 days of minute-by-minute data
    df = loader.generate_synthetic_data(n_samples=15000)
    
    # Format the timestamp column for better readability in Excel/CSV
    # It already comes in ISO format, but let's make sure it's consistent
    
    # Determine the output path
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, "predictive_maintenance_synthetic_dataset.csv")
    
    # Save the dataframe to CSV
    df.to_csv(output_path, index=False)
    
    print("\nDataset Generation Complete!")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Failures included: {df['is_failure'].sum()}")
    print(f"Upcoming failures (within horizon): {df['target'].sum()}")
    print(f"\nDataset saved successfully to: \n{output_path}")

if __name__ == "__main__":
    main()
