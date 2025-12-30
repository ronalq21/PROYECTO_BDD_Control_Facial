# e:\FINESI 5\base de datos 2\segunda unidad\reconocimiento facil\entrenar_modelo.py
import cv2
import os
import numpy as np
from tkinter import messagebox

def entrenar_modelo(data_path, modelo_dir, progress_callback=None):
    """
    Entrena el modelo de reconocimiento facial con las imágenes en la carpeta 'data'.
    Acepta un callback opcional para reportar el progreso.
    """
    print("Iniciando entrenamiento...")
    labels = []
    facesData = []

    if not os.path.exists(data_path) or not os.listdir(data_path):
        messagebox.showerror("Error de Entrenamiento", "La carpeta 'data' está vacía. No se puede entrenar el modelo.")
        return

    # --- 1. Contar el total de imágenes para la barra de progreso ---
    total_images = 0
    lista_personas_temp = os.listdir(data_path)
    for person_id_str in lista_personas_temp:
        personPath = os.path.join(data_path, person_id_str)
        if os.path.isdir(personPath):
            try:
                int(person_id_str) # Verificar si el nombre de la carpeta es un número (ID)
                total_images += len(os.listdir(personPath))
            except ValueError:
                continue # Omitir carpetas no numéricas

    if progress_callback:
        progress_callback(0, total_images) # Iniciar progreso en 0

    # --- 2. Leer las imágenes y actualizar el progreso ---
    # Aseguramos que las carpetas se lean en orden numérico, igual que en el script de reconocimiento.
    lista_personas_str = os.listdir(data_path)

    for person_id_str in lista_personas_str:
        personPath = os.path.join(data_path, person_id_str)
        print('Leyendo las imágenes de la persona con ID:', person_id_str)

        images_processed = 0
        try:
            # La etiqueta para el entrenamiento será el propio ID de la persona (convertido a entero)
            label = int(person_id_str)
            for fileName in os.listdir(personPath):
                labels.append(label)
                facesData.append(cv2.imread(os.path.join(personPath, fileName), 0))
                images_processed += 1
                if progress_callback:
                    progress_callback(len(facesData), total_images)
        except ValueError:
            print(f"Omitiendo carpeta con nombre no numérico: {person_id_str}")

    if not facesData:
        messagebox.showerror("Error de Entrenamiento", "No se encontraron rostros para entrenar.")
        return

    # --- 3. Selección inteligente del algoritmo y entrenamiento ---
    # FisherFace necesita al menos 2 clases (personas) diferentes.
    # Si solo hay una persona, usamos EigenFace que sí puede entrenar con una sola.
    modelo_eigen_path = os.path.join(modelo_dir, 'modeloEigenFace.xml')
    modelo_fisher_path = os.path.join(modelo_dir, 'modeloFisherFace.xml')

    # Limpiamos modelos antiguos para evitar conflictos
    if os.path.exists(modelo_eigen_path):
        os.remove(modelo_eigen_path)
    if os.path.exists(modelo_fisher_path):
        os.remove(modelo_fisher_path)

    # Usamos FisherFace si hay al menos 2 personas diferentes
    if len(np.unique(labels)) >= 2:
        print("Entrenando con FisherFace Recognizer (para 2 o más personas).")
        face_recognizer = cv2.face.FisherFaceRecognizer_create()
        modelo_a_guardar = modelo_fisher_path
    else:
        print("Entrenando con EigenFace Recognizer (para 1 persona).")
        face_recognizer = cv2.face.EigenFaceRecognizer_create()
        modelo_a_guardar = modelo_eigen_path

    # Entrenando el reconocedor de rostros
    print("Entrenando...")
    face_recognizer.train(facesData, np.array(labels))

    # Guardando el modelo obtenido
    face_recognizer.write(modelo_a_guardar)
    print("Modelo almacenado en:", modelo_a_guardar)

    # --- 4. Finalizar el progreso ---
    if progress_callback:
        progress_callback(total_images, total_images)
    messagebox.showinfo("Entrenamiento Completado", "El modelo ha sido entrenado y guardado exitosamente.")