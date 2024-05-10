import os

# Define the folder path
folder_path = r'C:\Users\Ghayur Haider\Desktop\AZ\Git\Salaah\2024 times\Images'

# Function to rename files
def rename_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg"):
            # parts = filename.split("_")
            # year = parts[0].split(" ")[0]
            # month_num = parts[1].split("-")[1][2:4]
            # if month_num:
            temp1 = filename.split(".jpg")[0]
            new_filename = f"{temp1[:4]}-{temp1[-2:]}.jpg"
            os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, new_filename))
            print(f"Renamed {filename} to {new_filename}")

# Call the function to rename files in the folder
rename_files(folder_path)