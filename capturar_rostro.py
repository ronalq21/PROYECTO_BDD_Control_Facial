import cv2
import os
import imutils
from tkinter import messagebox

def iniciar_captura(personId, personName, dataPath):
	"""
	Inicia la captura de rostros para un nuevo usuario.
	Usa el ID de la persona para nombrar la carpeta.
	"""
	personPath = os.path.join(dataPath, personId)

	if not os.path.exists(personPath):
		print('Carpeta creada: ',personPath)
		os.makedirs(personPath)
	
	# Ya no es necesario advertir sobreescribir, ya que el ID es único.
	# Si se quisiera permitir "re-capturar", se podría añadir la lógica aquí.

	cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
	#cap = cv2.VideoCapture('E:/FINESI 5/base de datos 2/segunda unidad/reconocimiento facil/dino.mp4')

	faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
	count = 0
	max_capturas = 300 # Reducimos el número de capturas para un proceso más rápido

	while True:
		ret, frame = cap.read()
		if not ret: break
		frame =  imutils.resize(frame, width=640)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		auxFrame = frame.copy()

		faces = faceClassif.detectMultiScale(gray,1.3,5)

		for (x,y,w,h) in faces:
			cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)
			rostro = gray[y:y+h,x:x+w]
			rostro = cv2.resize(rostro, (150,150), interpolation=cv2.INTER_CUBIC)
			# --- MEJORA DE CALIDAD: Ecualización del Histograma ---
			# Se aplica también aquí para guardar imágenes de entrenamiento normalizadas.
			rostro = cv2.equalizeHist(rostro)
			cv2.imwrite(os.path.join(personPath, 'rostro_{}.jpg'.format(count)), rostro)
			count = count + 1
		
		# Mostrar el contador de capturas en la pantalla
		cv2.putText(frame, f'Capturas: {count}/{max_capturas}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
		cv2.imshow('frame',frame)

		k =  cv2.waitKey(1)
		if k == 27 or count >= max_capturas:
			break

	cap.release()
	cv2.destroyAllWindows()
	messagebox.showinfo("Registro Finalizado", f"Se han capturado {count} imágenes para {personName}.\n\nAhora, por favor, entrene el modelo.")