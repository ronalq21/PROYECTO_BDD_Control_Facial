import cv2
import os
import imutils
from tkinter import messagebox # Importar messagebox
import database # Usamos nuestro módulo de base de datos centralizado

def proceso_de_reconocimiento(data_path, modelo_path, stop_event, callback_finalizar, es_salida=False):
    """
    Función interna que encapsula la lógica de reconocimiento facial.
    Puede registrar tanto entradas como salidas.
    """
    # --- Carga inteligente del modelo ---
    modelo_eigen = os.path.join(modelo_path, 'modeloEigenFace.xml')
    modelo_fisher = os.path.join(modelo_path, 'modeloFisherFace.xml')

    tipo_modelo_str = ""
    face_recognizer = None  # Inicializar para evitar errores si no se carga el modelo

    if os.path.exists(modelo_fisher):
        tipo_modelo_str = "FisherFace"
        face_recognizer = cv2.face.FisherFaceRecognizer_create()
        face_recognizer.read(modelo_fisher)
    elif os.path.exists(modelo_eigen):
        tipo_modelo_str = "EigenFace"
        face_recognizer = cv2.face.EigenFaceRecognizer_create()
        face_recognizer.read(modelo_eigen)
    else:
        cv2.destroyAllWindows()
        messagebox.showerror("Error", "No se encontró un archivo de modelo entrenado (.xml). Por favor, entrene el modelo primero.")        
        return
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # --- Configuración específica para Entrada o Salida ---
    if es_salida:
        window_name = 'Reconocimiento de Salida'
        print(f"Cargando modelo {tipo_modelo_str} para SALIDA...")
    else:
        window_name = 'Reconocimiento de Entrada'
        print(f"Cargando modelo {tipo_modelo_str} para ENTRADA...")

    # Conjunto para llevar registro de las personas ya registradas en esta sesión
    asistencia_registrada_sesion = set()

    try:
        while True:
            # Si el evento de detener se activa desde el hilo principal, rompemos el bucle
            if stop_event.is_set():
                print(f"Señal de detención recibida, cerrando cámara de {window_name}.")
                break
            ret, frame = cap.read()
            if not ret: break
            frame = imutils.resize(frame, width=640)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            auxFrame = gray.copy()
    
            faces = faceClassif.detectMultiScale(gray, 1.3, 5)
    
            for (x, y, w, h) in faces:
                rostro = auxFrame[y:y+h, x:x+w]
                rostro = cv2.resize(rostro, (150, 150), interpolation=cv2.INTER_CUBIC)
                # --- MEJORA DE PRECISIÓN: Ecualización del Histograma ---
                # Normaliza el brillo y contraste de la imagen.
                rostro = cv2.equalizeHist(rostro)
                result = face_recognizer.predict(rostro)
    
                # Mostramos el resultado de la predicción (etiqueta y confianza)
                cv2.putText(frame, '{}'.format(result), (x, y-5), 1, 1.3, (255, 255, 0), 1, cv2.LINE_AA)
    
                # Umbrales razonables: Fisher: ~500-800, Eigen: ~4000-5000, LBPH: ~50-70
                confianza = result[1]
                reconocido = False
                if isinstance(face_recognizer, cv2.face.FisherFaceRecognizer) and confianza < 800:
                    reconocido = True
                elif isinstance(face_recognizer, cv2.face.EigenFaceRecognizer) and confianza < 5000:
                    reconocido = True
    
                if reconocido:
                    predicted_label = result[0]
                    # La etiqueta predicha AHORA es directamente el persona_id
                    persona_id = predicted_label
                    
                    # --- Obtener nombre y registrar asistencia ---
                    try:
                        # Buscamos el nombre de la persona en la BD usando el ID predicho
                        nombre_persona = database.obtener_nombre_persona(persona_id)
                        
                        # Mensaje y registro diferentes para entrada o salida
                        if es_salida:
                            mensaje = f"{nombre_persona} (Salida)"
                            if persona_id not in asistencia_registrada_sesion:
                                if database.registrar_asistencia_salida(persona_id, nombre_persona):
                                    print(f"Salida registrada por primera vez hoy para: {nombre_persona}")
                                    asistencia_registrada_sesion.add(persona_id)
                        else: # Es entrada
                            mensaje = f"{nombre_persona}"
                            if persona_id not in asistencia_registrada_sesion:
                                if database.registrar_asistencia(persona_id, nombre_persona):
                                    print(f"Asistencia registrada por primera vez hoy para: {nombre_persona}")
                                    asistencia_registrada_sesion.add(persona_id)
                        
                        cv2.putText(frame, mensaje, (x, y-25), 2, 1.1, (0, 255, 0), 1, cv2.LINE_AA)
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    except Exception as e:
                        print(f"Error al procesar la predicción para el ID {persona_id}: {e}")
                else:
                    cv2.putText(frame, 'Desconocido', (x, y-25), 2, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
    
            cv2.imshow(window_name, frame)
            k = cv2.waitKey(1)
            if k == 27: # Si se presiona ESC
                break

    finally:
        print(f"Cámara de '{window_name}' liberada.")
        cap.release()
        cv2.destroyAllWindows()
        # Llama a la función de callback para notificar al hilo principal que hemos terminado
        if callback_finalizar:
            callback_finalizar()

def iniciar_reconocimiento(data_path, modelo_path, stop_event, callback_finalizar):
    """
    Inicia el proceso de reconocimiento facial y registra la ENTRADA.
    """
    proceso_de_reconocimiento(data_path, modelo_path, stop_event, callback_finalizar, es_salida=False)


def iniciar_reconocimiento_salida(data_path, modelo_path, stop_event, callback_finalizar):
    """
    Inicia el proceso de reconocimiento facial para registrar la SALIDA.
    """
    proceso_de_reconocimiento(data_path, modelo_path, stop_event, callback_finalizar, es_salida=True)
