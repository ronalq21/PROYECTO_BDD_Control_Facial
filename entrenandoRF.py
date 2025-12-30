# e:\FINESI 5\base de datos 2\segunda unidad\reconocimiento facil\entrenar_modelo.py
import cv2
import os
import numpy as np
from tkinter import messagebox

def entrenar_modelo(data_path):
    """Lee las imágenes y entrena el modelo de reconocimiento facial."""
    print("Iniciando entrenamiento...")
    labels = []
    facesData = []
    label = 0

    if not os.path.exists(data_path):
        print(f"Error: La ruta de datos '{data_path}' no existe.")
        messagebox.showerror("Error", f"La ruta de datos '{data_path}' no existe.")
        return

    # Los nombres de las carpetas son los IDs de las personas
    person_folders = os.listdir(data_path)
    print("Leyendo imágenes...")

    for person_id_str in person_folders:
        person_path = os.path.join(data_path, person_id_str)
        if not os.path.isdir(person_path):
            continue
        
        try:
            # El nombre de la carpeta es el ID, que usamos como etiqueta
            label = int(person_id_str)
            for file_name in os.listdir(person_path):
                image_path = os.path.join(person_path, file_name)
                image = cv2.imread(image_path, 0) # Leer en escala de grises
                if image is None:
                    print(f"No se pudo leer la imagen {image_path}")
                    continue
                facesData.append(image)
                labels.append(label)
        except ValueError:
            print(f"La carpeta '{person_id_str}' no es un ID válido. Se omitirá.")
            continue

    if not facesData:
        print("No se encontraron caras para entrenar.")
        messagebox.showwarning("Advertencia", "No se encontraron caras para entrenar. Asegúrate de registrar usuarios primero.")
        return

    print(f"Se encontraron {len(np.unique(labels))} usuarios únicos.")
    
    # Crear el reconocedor y entrenarlo
    face_recognizer = cv2.face.FisherFaceRecognizer_create()
    print("Entrenando el modelo FisherFace...")
    face_recognizer.train(facesData, np.array(labels))

    # Guardar el modelo entrenado
    modelo_path = 'modeloFisherFace.xml'
    face_recognizer.write(modelo_path)
    print(f"Modelo guardado en '{modelo_path}'")
    messagebox.showinfo("Entrenamiento completado", f"¡Modelo entrenado y guardado exitosamente en '{modelo_path}'!")

if __name__ == '__main__':
    # Para ejecutar este archivo directamente si es necesario
    dataPath = 'E:/FINESI 5/base de datos 2/segunda unidad/reconocimiento facil/data'
    entrenar_modelo(dataPath)
