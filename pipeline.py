import os
import shutil

FROM_FOLDER = "from/"
TO_FOLDER = "to/"

#ensures that the from and to folders exist
os.makedirs(FROM_FOLDER, exist_ok=True)
os.makedirs(TO_FOLDER, exist_ok=True)

#print to ensure they are found and ready
print(f"Folders '{FROM_FOLDER}' and '{TO_FOLDER}' are ready")

#clears the to folder by looping through all files in the to folder and deleting them
def clear_to_folder():
    if os.path.exists(TO_FOLDER):
        #print to know deletion works
        print(f"Deleting all contents inside '{TO_FOLDER}'")
        for filename in os.listdir(TO_FOLDER): 
            file_path = os.path.join(TO_FOLDER, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path) 
            except Exception as e:
                print(f"Failed to delete some files in '{TO_FOLDER}'. Reason: {e}")

#copies all the dicom files from the from folder to the to folder
def copy_dicom_files():
    #flag to check if any .dcm files were found
    found_files = False

    ##loops through all the folders in the from folder and all sub folders
    for root, _, files in os.walk(FROM_FOLDER): 
        for filename in files:  
            if filename.endswith(".dcm"): 
                found_files = True
                source_path = os.path.join(root, filename)
                new_filename = f"edited_{filename}"
                destination_path = os.path.join(TO_FOLDER, new_filename)
                
                #copies and renames the files
                try:
                    shutil.copy2(source_path, destination_path)  
                except Exception as e:
                    print(f"Failed to copy some files from '{FROM_FOLDER}'. Reason: {e}")

    #prints if any files were found or not
    if found_files:
        print(f"Copied .dcm files from '{FROM_FOLDER}' to '{TO_FOLDER}'")
    else:
        print(f"No .dcm files found in '{FROM_FOLDER}' or its subfolders.")

#clears the to folder and moves files from the from folder to the to folder with a new name
def move_and_rename_dicom_files():
    clear_to_folder()  
    copy_dicom_files()  

move_and_rename_dicom_files()
