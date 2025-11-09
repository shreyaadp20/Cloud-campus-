import pandas as pd
from supabase import create_client
import os

# Use environment variables for security
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://vlainnzrdnhqlrlzwysq.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Set this in environment variables

if not SUPABASE_KEY:
    print("Error: SUPABASE_KEY environment variable not set")
    exit(1)

# Create client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client created successfully!")
except Exception as e:
    print(f"❌ Failed to create Supabase client: {e}")
    exit(1)

def upload_csv_to_supabase(csv_path, table_name="kaggle", batch_size=100):
    """Upload CSV data to Supabase in batches"""
    try:
        # Load CSV
        df = pd.read_csv(csv_path)
        print(f"✅ CSV loaded successfully! Rows: {len(df)}, Columns: {len(df.columns)}")
        print(f"Columns: {list(df.columns)}")
        
        # Convert to list of dictionaries
        data = df.to_dict('records')
        total_rows = len(data)
        
        print(f"🔄 Starting upload of {total_rows} rows to table '{table_name}'...")
        
        # Upload in batches
        successful_uploads = 0
        for i in range(0, total_rows, batch_size):
            batch = data[i:i + batch_size]
            try:
                response = supabase.table(table_name).insert(batch).execute()
                
                if hasattr(response, 'error') and response.error:
                    print(f"❌ Error in batch {i//batch_size + 1}: {response.error}")
                else:
                    successful_uploads += len(batch)
                    print(f"✅ Batch {i//batch_size + 1}: Uploaded {len(batch)} rows")
                    
            except Exception as e:
                print(f"❌ Exception in batch {i//batch_size + 1}: {e}")
        
        print(f"🎉 Upload complete! Successfully uploaded {successful_uploads}/{total_rows} rows")
        
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_path}")
    except Exception as e:
        print(f"❌ Error during upload: {e}")

# Usage
if __name__ == "__main__":
    csv_path = "kaggle_raw.csv"  # Make sure this file exists
    upload_csv_to_supabase(csv_path)
