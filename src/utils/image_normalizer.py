import os

folder_path = './images'

def force_normalize(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            new_name = filename.lower().replace(' ', '-')

            if filename != new_name:
                old_file = os.path.join(directory, filename)
                new_file = os.path.join(directory, new_name)
                
                try:
                    os.rename(old_file, new_file)
                    print(f"Renombrado: '{filename}' -> '{new_name}'")
                except Exception as e:
                    print(f"Error al renombrar '{filename}': {e}")
            else:
                pass

if __name__ == "__main__":
    force_normalize(folder_path)
    print("Proceso finalizado.")