import os

# Define the folder path
folder_path = r'C:\Users\Ghayur Haider\Desktop\AZ\Git\Salaah\2024 times\Images'

# Function to rename files
def rename_files(folder_path):
    for filename in os.listdir(folder_path):
        if "times_page-" in filename and filename.endswith(".jpg"):
            parts = filename.split("_")
            year = parts[0].split(" ")[0]
            month_num = parts[1].split("-")[1][2:4]
            if month_num:
                new_filename = f"{year}-{month_num}.jpg"
                os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, new_filename))
                print(f"Renamed {filename} to {new_filename}")
            else:
                print(f"Could not find month for {filename}")

# Call the function to rename files in the folder
rename_files(folder_path)