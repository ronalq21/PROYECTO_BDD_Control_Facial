# e:\FINESI 5\base de datos 2\segunda unidad\reconocimiento facil\app_principal.py
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
from tkinter.font import Font
import os
import threading
import sys
import csv
from datetime import datetime
from tkcalendar import DateEntry # Importar el selector de fechas
import bcrypt # Necesario para verificar la contraseña
# Importamos los módulos que hemos creado
import capturar_rostro
import entrenar_modelo # Importamos el módulo para entrenar el delo
import database # Importamos el nuevo módulo de base de datos
import shutil # Importar shutil para eliminar directorios
import ReconocimientoFacial

# --- Configuración ---
# Usa una ruta absoluta para evitar problemas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data')

MODELO_DIR = BASE_DIR 

class VentanaLogin(tk.Toplevel):
    """Ventana de inicio de sesión."""
    def __init__(self, parent, root_app, callback_exito):
        super().__init__(parent)
        self.root_app = root_app # Referencia a la ventana principal tk.Tk()
        self.callback_exito = callback_exito

        self.title("Inicio de Sesión")
        self.geometry("400x380")
        self.resizable(False, False)
        self.configure(bg='#ffffff')
        self.center_window() # Centrar la ventana de login

        # Hacer la ventana modal
        self.transient(parent)
        self.grab_set()

        # --- Frame principal con un fondo blanco ---
        main_frame = tk.Frame(self, bg='#ffffff', padx=40, pady=30)
        main_frame.pack(expand=True, fill='both')
        main_frame.grid_columnconfigure(0, weight=1)

        # --- Título ---
        tk.Label(main_frame, text="Bienvenido", font=("Segoe UI", 22, "bold"), bg='#ffffff').grid(row=0, column=0, columnspan=2, pady=(0, 10))
        tk.Label(main_frame, text="Inicia sesión para continuar", font=("Segoe UI", 11), bg='#ffffff', fg="#555555").grid(row=1, column=0, columnspan=2, pady=(0, 25))

        # --- Campo de Usuario (DNI) con icono ---
        tk.Label(main_frame, text="👤 Usuario (DNI)", font=("Segoe UI", 11), bg='#ffffff').grid(row=2, column=0, columnspan=2, sticky='w', pady=(0,5))
        self.entry_dni = ttk.Entry(main_frame, font=("Segoe UI", 12), width=30)
        self.entry_dni.grid(row=3, column=0, columnspan=2, sticky='ew', ipady=4, pady=(0, 15))
        self.entry_dni.focus_set()

        # --- Campo de Contraseña con icono ---
        tk.Label(main_frame, text="🔒 Contraseña", font=("Segoe UI", 11), bg='#ffffff').grid(row=4, column=0, columnspan=2, sticky='w', pady=(0,5))
        self.entry_contrasena = ttk.Entry(main_frame, font=("Segoe UI", 12), show='*', width=30)
        self.entry_contrasena.grid(row=5, column=0, columnspan=2, sticky='ew', ipady=4, pady=(0, 20))

        # --- Botón de Iniciar Sesión ---
        # Definimos un estilo personalizado para el botón de login
        style = ttk.Style(self)
        style.configure('Login.TButton', font=("Segoe UI", 12, "bold"), foreground="white", background="#002CF1")
        style.map('Login.TButton', background=[('active', '#0056b3')])

        btn_login = ttk.Button(main_frame, text="Iniciar Sesión", command=self._intentar_login, style='Login.TButton', cursor="hand2")
        btn_login.grid(row=6, column=0, columnspan=2, sticky='ew', ipady=8)

        # Vincular Enter para iniciar sesión
        self.bind('<Return>', lambda event: self._intentar_login())
        
        # Si el usuario cierra la ventana de login, se cierra toda la aplicación
        self.protocol("WM_DELETE_WINDOW", self.root_app.destroy) # Cerrar la aplicación principal

    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _intentar_login(self):
        dni = self.entry_dni.get().strip()
        contrasena = self.entry_contrasena.get()

        if not dni or not contrasena:
            messagebox.showerror("Error", "Ambos campos son obligatorios.", parent=self)
            return

        # --- ACCESO ESPECIAL DE SUPERADMINISTRADOR ---
        # Primero, verificamos si las credenciales coinciden con el acceso maestro.
        if dni == '75580218' and contrasena == 'vidman18':
            print("Acceso de superadministrador concedido.")
            self.callback_exito() # Llama a la función para mostrar la app principal
            self.destroy() # Cierra la ventana de login
        # Si no son las credenciales maestras, se procede con la verificación normal en la base de datos.
        elif database.verificar_usuario(dni, contrasena):
            print(f"Acceso concedido para el usuario con DNI: {dni}")
            self.callback_exito()
            self.destroy()
        else:
            messagebox.showerror("Error de Autenticación", "DNI o contraseña incorrectos.", parent=self)

class VentanaRegistro(tk.Toplevel):
    """Ventana personalizada para el registro de nuevos usuarios."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Registrar Persona para Reconocimiento")
        self.geometry("450x280")
        self.configure(bg='#f0f2f5')        
        self.resizable(False, False)
        self.transient(parent) # Mantener por encima de la ventana principal
        self.grab_set() # Modal

        style = ttk.Style(self)
        style.configure('Stop.TButton', background='#6c757d', foreground='white')
        style.map('Stop.TButton', background=[('active', '#5a6268')])

        main_frame = tk.Frame(self, bg='#f0f2f5', padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        main_frame.grid_columnconfigure(0, weight=1)

        # --- Campos del formulario ---
        tk.Label(main_frame, text="Nombre Completo:", font=("Segoe UI", 11), bg='#f0f2f5').grid(row=0, column=0, sticky='w')
        self.entry_nombre_completo = ttk.Entry(main_frame, font=("Segoe UI", 11))
        self.entry_nombre_completo.grid(row=1, column=0, sticky='ew', pady=(2, 15))
        self.entry_nombre_completo.focus_set()

        info_text = "Se tomarán 300 fotos. Gira tu cabeza lentamente frente a la cámara para capturar diferentes ángulos de tu rostro."
        label_info = tk.Label(main_frame, text=info_text, wraplength=350, justify='left', font=("Segoe UI", 9), bg='#e9ecef', fg='#495057', padx=10, pady=10)
        label_info.grid(row=2, column=0, sticky='ew', pady=(5, 15))

        # --- Botones ---
        btn_iniciar = ttk.Button(main_frame, text="Iniciar Captura de Rostro", command=self._iniciar_captura)
        btn_iniciar.grid(row=3, column=0, sticky='ew', ipady=5)

        # Vincular la tecla Enter al botón de iniciar
        self.bind('<Return>', lambda event: self._iniciar_captura())

    def _iniciar_captura(self):
        nombre_completo = self.entry_nombre_completo.get().strip()

        if not nombre_completo:
            messagebox.showerror("Error de Validación", "El campo 'Nombre Completo' es obligatorio.", parent=self)
            return

        # 1. Registrar la persona en la tabla 'personas' y obtener el ID generado.
        persona_id = database.registrar_y_obtener_persona(nombre_completo)

        # 2. Si se registró correctamente (se obtuvo un ID), iniciar la captura.
        if persona_id:
            self.destroy() # Cerrar la ventana de registro
            capturar_rostro.iniciar_captura(str(persona_id), nombre_completo, DATA_PATH)

class VentanaAdmin(tk.Toplevel):
    """Ventana para la administración de usuarios."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Administración de Usuarios")
        self.geometry("1200x700") # Ancho aumentado para las nuevas columnas
        self.configure(bg='#f0f2f5')
        self.minsize(980, 700) # Establecer un tamaño mínimo
        self.transient(parent)
        self.grab_set()
        self.id_usuario_editando = None # Para saber si estamos en modo edición

        # --- Frame principal ---
        main_frame = ttk.Frame(self, padding="10")

        # --- Frame para el formulario de creación ---
        form_frame = ttk.LabelFrame(main_frame, text="Crear Nuevo Usuario", padding="10")
        form_frame.pack(fill='x', pady=(0, 10))
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)
        form_frame.grid_columnconfigure(5, weight=1)

        # Campos del formulario
        ttk.Label(form_frame, text="Usuario:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.entry_user = ttk.Entry(form_frame)
        self.entry_user.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(form_frame, text="Contraseña:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.entry_pass = ttk.Entry(form_frame, show="*")
        self.entry_pass.grid(row=0, column=3, padx=5, pady=5, sticky='ew')

        ttk.Label(form_frame, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.entry_nombre = ttk.Entry(form_frame)
        self.entry_nombre.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(form_frame, text="Apellido:").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        self.entry_apellido = ttk.Entry(form_frame)
        self.entry_apellido.grid(row=1, column=3, padx=5, pady=5, sticky='ew')

        ttk.Label(form_frame, text="DNI:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.entry_dni = ttk.Entry(form_frame)
        self.entry_dni.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(form_frame, text="Correo E:").grid(row=2, column=2, padx=5, pady=5, sticky='w')
        self.entry_correo = ttk.Entry(form_frame)
        self.entry_correo.grid(row=2, column=3, padx=5, pady=5, sticky='ew')

        ttk.Label(form_frame, text="Celular:").grid(row=2, column=4, padx=5, pady=5, sticky='w')
        self.entry_celular = ttk.Entry(form_frame)
        self.entry_celular.grid(row=2, column=5, padx=5, pady=5, sticky='ew')

        # Frame para los botones del formulario
        form_button_frame = ttk.Frame(form_frame)
        form_button_frame.grid(row=3, column=0, columnspan=6, padx=5, pady=10, sticky='e')

        self.btn_limpiar_cancelar = ttk.Button(form_button_frame, text="Limpiar", command=self.limpiar_campos, style='Stop.TButton')
        self.btn_limpiar_cancelar.pack(side='left', padx=(0, 5))

        self.btn_crear_guardar = ttk.Button(form_button_frame, text="Crear Usuario", command=self.crear_o_guardar_usuario)
        self.btn_crear_guardar.pack(side='left')

        # --- Frame para la lista de usuarios ---
        list_frame = ttk.LabelFrame(main_frame, text="Usuarios Registrados", padding="10")
        list_frame.pack(expand=True, fill='both', pady=(10, 0))

        columnas = ('id', 'usuario', 'contrasena', 'nombre', 'apellido', 'dni', 'correo', 'celular')
        self.tree_usuarios = ttk.Treeview(list_frame, columns=columnas, show='headings')
        self.tree_usuarios.heading('id', text='ID')
        self.tree_usuarios.heading('usuario', text='Usuario')
        self.tree_usuarios.heading('contrasena', text='Contraseña')
        self.tree_usuarios.heading('nombre', text='Nombre')
        self.tree_usuarios.heading('apellido', text='Apellido')
        self.tree_usuarios.heading('dni', text='DNI')
        self.tree_usuarios.heading('correo', text='Correo')
        self.tree_usuarios.heading('celular', text='Celular')

        self.tree_usuarios.column('id', width=50, anchor='center')
        self.tree_usuarios.column('correo', width=180)
        self.tree_usuarios.column('celular', width=100, anchor='center')
        self.tree_usuarios.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree_usuarios.yview)
        self.tree_usuarios.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # --- Frame para botones de acción (Editar, Eliminar) ---
        action_button_frame = ttk.Frame(main_frame)
        action_button_frame.pack(pady=10)

        btn_editar = ttk.Button(action_button_frame, text="Editar Usuario Seleccionado", command=self.iniciar_edicion_usuario)
        btn_editar.pack(side='left', padx=(0, 10))

        btn_eliminar = ttk.Button(action_button_frame, text="Eliminar Usuario Seleccionado", command=self.eliminar_usuario, style='Stop.TButton')
        btn_eliminar.pack(side='left')

        # Empaquetar el frame principal al final para que los otros widgets se dibujen primero
        main_frame.pack(expand=True, fill="both")

        self.cargar_usuarios()

    def cargar_usuarios(self):
        for i in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(i)
        
        usuarios = database.obtener_todos_los_usuarios()
        for user in usuarios:
            # CORREGIDO: Se insertan todos los valores requeridos por el Treeview.
            # Se usa user.get('contrasena_plana', '') para evitar errores si el valor es nulo.
            self.tree_usuarios.insert('', 'end', iid=user['id'], values=(
                user['id'], user['nombre_usuario'], user.get('contrasena_plana', ''), user['nombre'], 
                user['apellido'], user['dni'], user.get('correo', ''), user.get('celular', '')
            ))



    def crear_o_guardar_usuario(self):
        nombre_usuario = self.entry_user.get().strip()
        contrasena = self.entry_pass.get().strip()
        nombre = self.entry_nombre.get().strip()
        apellido = self.entry_apellido.get().strip()
        dni = self.entry_dni.get().strip()
        correo = self.entry_correo.get().strip()
        celular = self.entry_celular.get().strip()

        if self.id_usuario_editando:
            # --- Lógica para GUARDAR CAMBIOS ---
            if not all([nombre_usuario, nombre, apellido, dni]):
                messagebox.showerror("Error", "Los campos Usuario, Nombre, Apellido y DNI son obligatorios.", parent=self)
                return
            
            # Si los campos de admin están deshabilitados, usamos sus valores originales
            if self.entry_user.cget("state") == "disabled":
                nombre_usuario = self.entry_user.get()
            if self.entry_dni.cget("state") == "disabled":
                dni = self.entry_dni.get()

            if database.actualizar_usuario(self.id_usuario_editando, nombre_usuario, nombre, apellido, dni, correo, celular, contrasena):
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente.", parent=self)
                self.cargar_usuarios()
                self.limpiar_campos() # Esto también sale del modo edición
            else:
                # El mensaje de error específico ya lo muestra la función de database
                pass
        else:
            # --- Lógica para CREAR USUARIO ---
            if not all([nombre_usuario, contrasena, nombre, apellido, dni]):
                messagebox.showerror("Error", "Todos los campos son obligatorios para crear un nuevo usuario.", parent=self)
                return

            if database.crear_usuario(nombre_usuario, contrasena, nombre, apellido, dni, correo, celular):
                messagebox.showinfo("Éxito", "Usuario creado correctamente.", parent=self)
                self.cargar_usuarios()
                self.limpiar_campos()
            else:
                # El mensaje de error específico ya lo muestra la función de database
                pass
    def limpiar_campos(self):
        """Limpia todos los campos de entrada del formulario."""
        self.entry_user.delete(0, 'end')
        self.entry_pass.delete(0, 'end')
        self.entry_nombre.delete(0, 'end')
        self.entry_apellido.delete(0, 'end')
        self.entry_dni.delete(0, 'end')
        self.entry_correo.delete(0, 'end')
        self.entry_celular.delete(0, 'end')
        self.entry_user.focus_set() # Poner el foco en el primer campo

        # Salir del modo edición si estábamos en él
        if self.id_usuario_editando is not None:
            self.id_usuario_editando = None
            self.title("Administración de Usuarios")
            self.btn_crear_guardar.config(text="Crear Usuario")
            self.btn_limpiar_cancelar.config(text="Limpiar")
            self.entry_dni.config(state='normal') # Habilitar campo DNI
            self.entry_user.config(state='normal') # Habilitar campo Usuario


    def iniciar_edicion_usuario(self):
        """Carga los datos del usuario seleccionado en el formulario para editarlos."""
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un usuario para editar.", parent=self)
            return

        item = self.tree_usuarios.item(seleccion[0])
        valores = item['values']
        
        id_usuario = valores[0]
        nombre_usuario = valores[1]
        nombre = valores[3]
        apellido = valores[4]
        dni = valores[5]
        correo = valores[6]
        celular = valores[7]

        # Limpiar campos antes de llenarlos
        self.limpiar_campos()

        # Llenar el formulario con los datos del usuario
        self.entry_user.insert(0, nombre_usuario)
        self.entry_nombre.insert(0, nombre)
        self.entry_apellido.insert(0, apellido)
        self.entry_dni.insert(0, dni)
        self.entry_correo.insert(0, correo)
        self.entry_celular.insert(0, celular)

        # Entrar en modo edición
        self.id_usuario_editando = id_usuario
        self.title(f"Editando Usuario: {nombre_usuario} (ID: {id_usuario})")
        self.btn_crear_guardar.config(text="Guardar Cambios")
        self.btn_limpiar_cancelar.config(text="Cancelar Edición")

        # No permitir cambiar el DNI ni el nombre de usuario del admin principal
        if dni == '75580218':
            self.entry_dni.config(state='disabled')
            self.entry_user.config(state='disabled')

    def eliminar_usuario(self):
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un usuario para eliminar.", parent=self)
            return

        item = self.tree_usuarios.item(seleccion[0])
        # Corregido: Los índices de 'values' deben coincidir con el orden de las columnas
        # ('id', 'usuario', 'contrasena', 'nombre', 'apellido', 'dni', 'correo', 'celular')
        id_usuario = item['values'][0] # ID está en el índice 0
        nombre_usuario = item['values'][3] # Nombre está en el índice 3
        apellido_usuario = item['values'][4] # Apellido está en el índice 4
        dni_usuario = item['values'][5] # DNI está en el índice 5

        # Protección para no eliminar al usuario administrador principal
        if dni_usuario == '75580218':
            messagebox.showerror("Acción no permitida", "No se puede eliminar al usuario administrador principal.", parent=self)
            return

        # Corregido: Mostrar el nombre y apellido correctos en el mensaje de confirmación
        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar al usuario con ID {id_usuario} ({nombre_usuario} {apellido_usuario})?", parent=self):
            if database.eliminar_usuario(id_usuario):
                messagebox.showinfo("Éxito", "Usuario eliminado correctamente.", parent=self)
                self.cargar_usuarios()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el usuario.", parent=self)

class PasswordDialog(tk.Toplevel):
    """Diálogo personalizado y más presentable para solicitar la contraseña de administrador."""
    def __init__(self, parent):
        super().__init__(parent)
        self.password = None  # Para almacenar la contraseña ingresada

        self.title("Acceso Restringido")
        self.geometry("350x190")
        self.resizable(False, False)
        self.configure(bg='#f0f2f5')
        self.transient(parent)
        self.grab_set()

        # Centrar la ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')

        main_frame = tk.Frame(self, bg='#f0f2f5', padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        main_frame.grid_columnconfigure(0, weight=1)

        tk.Label(main_frame, text="Acceso de Administrador", font=("Segoe UI", 14, "bold"), bg='#f0f2f5').grid(row=0, column=0, sticky='w', pady=(0, 5))
        tk.Label(main_frame, text="Ingrese la contraseña para continuar.", font=("Segoe UI", 10), bg='#f0f2f5').grid(row=1, column=0, sticky='w', pady=(0, 10))

        self.entry_password = ttk.Entry(main_frame, font=("Segoe UI", 10), show='*')
        self.entry_password.grid(row=2, column=0, sticky='ew', pady=(5, 15))
        self.entry_password.focus_set()

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky='e')

        btn_aceptar = ttk.Button(button_frame, text="Aceptar", command=self._on_accept)
        btn_aceptar.pack(side='left')

        btn_cancelar = ttk.Button(button_frame, text="Cancelar", command=self.destroy, style='Stop.TButton')
        btn_cancelar.pack(side='left', padx=(5, 0))

        self.bind('<Return>', lambda event: self._on_accept())
        self.bind('<Escape>', lambda event: self.destroy())

    def _on_accept(self):
        self.password = self.entry_password.get()
        self.destroy()


def entrenar_modelo_wrapper():
    """Función envoltorio para entrenar el modelo."""
    entrenar_modelo.entrenar_modelo(DATA_PATH, MODELO_DIR)

class TextRedirector(object):
    """Una clase para redirigir la salida de texto (como print) a un widget de Tkinter."""
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        # Usamos `after` para asegurarnos de que la actualización de la GUI se haga en el hilo principal
        self.widget.after(0, self.write_ui, str)

    def write_ui(self, str):
        self.widget.configure(state='normal')
        self.widget.insert('end', str, (self.tag,))
        self.widget.see('end')
        self.widget.configure(state='disabled')

class App:
    def __init__(self, root):
        self.root = root
        self.stop_event = None
        self.recognition_thread = None
        self.root.title("Sistema de Reconocimiento Facial")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing) # Guardar geometría al cerrar

        self._setup_styles()
        self._setup_ui()
        self._redirect_console_output()

    def _setup_styles(self):
        """Configura los estilos para los widgets de la aplicación."""
        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        # Estilo general de botones
        button_font = Font(family="Segoe UI", size=12)
        style.configure('TButton', font=button_font, padding=10, borderwidth=0)
        style.map('TButton',
                  foreground=[('!active', 'white'), ('active', 'white')],
                  background=[('!active', '#007bff'), ('active', '#0056b3')])

        # Estilo para el botón de detener
        style.configure('Stop.TButton', background='#dc3545', foreground='white')
        style.map('Stop.TButton', background=[('active', '#c82333')])

    def _setup_ui(self):
        """Configura la interfaz de usuario de la ventana principal."""
        self._load_geometry() # Cargar la última geometría guardada
        self.root.configure(bg='#f0f2f5')
        self.root.resizable(True, True)

        self._create_header()
        self._create_notebook()
        self._create_log_console()
        self._create_footer()

    def _load_geometry(self):
        """Carga la geometría de la ventana desde un archivo de configuración."""
        try:
            with open("config.ini", "r") as f:
                geometry = f.read()
                self.root.geometry(geometry)
        except FileNotFoundError:
            # Si el archivo no existe, usar una geometría por defecto y centrar
            self.root.geometry("900x700")
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _on_closing(self):
        """Se ejecuta al cerrar la ventana. Guarda la geometría y cierra la app."""
        with open("config.ini", "w") as f:
            f.write(self.root.geometry())
        self.root.destroy()

    def _create_header(self):
        header_frame = tk.Frame(root, bg='#ffffff', pady=15)
        header_frame.pack(fill='x')
        title_font = Font(family="Segoe UI", size=20, weight="bold")
        label_titulo = tk.Label(header_frame, text="Sistema de Asistencia", font=title_font, bg='#ffffff', fg='#333')
        label_titulo.pack()

    def _create_notebook(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        menu_tab = ttk.Frame(notebook, padding="10")
        notebook.add(menu_tab, text='Menú Principal')
        self._create_menu_tab(menu_tab)

        report_tab = ttk.Frame(notebook, padding="10")
        notebook.add(report_tab, text='Reporte de Asistencia')
        self._create_report_tab(report_tab)

        # Pestaña para ver las personas registradas
        personas_tab = ttk.Frame(notebook, padding="10")
        notebook.add(personas_tab, text='Personas Registradas')
        self._create_personas_tab(personas_tab)

    def _create_log_console(self):
        log_frame = tk.Frame(self.root, bg='#f0f2f5')
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.log_text = tk.Text(log_frame, height=10, bg='black', fg='white', font=("Consolas", 9), state='disabled', relief='solid', borderwidth=1)
        self.log_text.pack(fill='both', expand=True)
        self.log_text.tag_config("stdout", foreground="white")
        self.log_text.tag_config("stderr", foreground="red")

    def _create_footer(self):
        footer_frame = tk.Frame(self.root, bg='#e9ecef', pady=5)
        footer_frame.pack(fill='x', side='bottom')
        label_footer = tk.Label(footer_frame, text="Desarrollado con OpenCV y Tkinter", font=("Segoe UI", 8), bg='#e9ecef', fg='#6c757d')
        label_footer.pack()

    def _create_menu_tab(self, tab):
        """Crea los widgets para la pestaña del menú principal."""
        # Frame para centrar los botones. Usamos ttk.Frame para que herede el estilo de la pestaña.
        button_container = ttk.Frame(tab)
        button_container.pack(expand=True)

        self.btn_registrar = ttk.Button(button_container, text="1. Registrar Nuevo", command=lambda: VentanaRegistro(self.root), style='TButton')
        self.btn_registrar.pack(pady=8, ipady=5, padx=20, fill='x')

        self.btn_entrenar = ttk.Button(button_container, text="2. Entrenar Modelo", command=entrenar_modelo_wrapper, style='TButton')
        self.btn_entrenar.pack(pady=8, ipady=5, padx=20, fill='x')

        self.btn_reconocer_entrada = ttk.Button(button_container, text="3. Iniciar Reconocimiento de Entrada", command=lambda: self._iniciar_reconocimiento_thread(es_salida=False), style='TButton')
        self.btn_reconocer_entrada.pack(pady=8, ipady=5, padx=20, fill='x')

        self.btn_reconocer_salida = ttk.Button(button_container, text="4. Iniciar Reconocimiento de Salida", command=lambda: self._iniciar_reconocimiento_thread(es_salida=True), style='TButton')
        self.btn_reconocer_salida.pack(pady=8, ipady=5, padx=20, fill='x')

        self.btn_admin = ttk.Button(button_container, text="5. Administrar Usuarios", command=self._abrir_admin_con_password, style='TButton')
        self.btn_admin.pack(pady=8, ipady=5, padx=20, fill='x')

        # Botón para detener el reconocimiento (inicialmente oculto)
        self.btn_detener = ttk.Button(button_container, text="Detener Reconocimiento", command=self._detener_reconocimiento, style='Stop.TButton')

    def _create_report_tab(self, tab):
        """Crea los widgets para la pestaña de reporte."""
        # --- Frame para controles (botones y fechas) ---
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill='x', pady=(0, 10))

        # --- Controles de Fecha ---
        ttk.Label(control_frame, text="Fecha Inicio:").pack(side='left', padx=(0, 5))
        self.fecha_inicio_entry = DateEntry(control_frame, width=12, background='darkblue',
                                            foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.fecha_inicio_entry.pack(side='left', padx=(0, 10))

        ttk.Label(control_frame, text="Fecha Fin:").pack(side='left', padx=(0, 5))
        self.fecha_fin_entry = DateEntry(control_frame, width=12, background='darkblue',
                                         foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.fecha_fin_entry.pack(side='left', padx=(0, 20))

        btn_actualizar = ttk.Button(control_frame, text="Filtrar", command=self._cargar_reporte)
        btn_actualizar.pack(side='left')
        
        btn_exportar = ttk.Button(control_frame, text="Exportar a CSV", command=self._exportar_csv)
        btn_exportar.pack(side='left', padx=10)

        # --- Frame para la tabla y el scrollbar ---
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(expand=True, fill='both')

        # --- Treeview para la tabla ---
        columnas = ('id', 'nombre', 'fecha', 'entrada', 'salida', 'horas_asistidas')
        self.report_tree = ttk.Treeview(tree_frame, columns=columnas, show='headings')

        # Estilo para filas alternadas
        self.report_tree.tag_configure('oddrow', background='#f0f2f5')
        self.report_tree.tag_configure('evenrow', background='#ffffff')

        # Definir encabezados
        self.report_tree.heading('id', text='ID')
        self.report_tree.heading('nombre', text='Nombre Completo')
        self.report_tree.heading('fecha', text='Fecha')
        self.report_tree.heading('entrada', text='Hora Entrada')
        self.report_tree.heading('salida', text='Hora Salida')
        self.report_tree.heading('horas_asistidas', text='Horas Asistidas')

        # Ajustar ancho de columnas
        self.report_tree.column('id', width=50, anchor='center')
        self.report_tree.column('nombre', width=250)
        self.report_tree.column('fecha', width=100, anchor='center')
        self.report_tree.column('entrada', width=100, anchor='center')
        self.report_tree.column('salida', width=100, anchor='center')
        self.report_tree.column('horas_asistidas', width=120, anchor='center')

        self.report_tree.pack(side='left', fill='both', expand=True)

        # --- Scrollbar ---
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self._cargar_reporte()

    def _redirect_console_output(self):
        """Redirige la salida de la consola al widget de texto."""
        stdout_redirector = TextRedirector(self.log_text, "stdout")
        stderr_redirector = TextRedirector(self.log_text, "stderr")
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def _abrir_admin_con_password(self):
        """Pide la contraseña principal antes de abrir la ventana de administración."""
        dialog = PasswordDialog(self.root)
        # El método wait_window pausa la ejecución aquí hasta que la ventana del diálogo se cierre
        self.root.wait_window(dialog)

        password = dialog.password
        
        # Verificar si la contraseña es correcta (la misma que el superadministrador)
        if password == 'vidman18':
            VentanaAdmin(self.root)
        elif password is not None: # Si el usuario ingresó algo pero es incorrecto
            messagebox.showerror("Acceso Denegado", "Contraseña incorrecta.", parent=self.root)
        # Si password es None (el usuario cerró el diálogo o presionó cancelar), no hacemos nada.

    def _iniciar_reconocimiento_thread(self, es_salida=False):
        """Inicia el reconocimiento facial en un hilo separado."""
        if not os.path.exists(DATA_PATH) or not os.listdir(DATA_PATH):
            messagebox.showerror("Error", "La carpeta 'data' está vacía. Por favor, registre al menos un usuario.")
            return

        self.stop_event = threading.Event()
        
        if es_salida:
            target_func = ReconocimientoFacial.iniciar_reconocimiento_salida
        else:
            target_func = ReconocimientoFacial.iniciar_reconocimiento

        self.recognition_thread = threading.Thread(
            target=target_func,
            args=(DATA_PATH, MODELO_DIR, self.stop_event, self._finalizar_reconocimiento_ui)
        )
        self.recognition_thread.start()
        self._actualizar_ui_para_reconocimiento(iniciado=True)

    def _detener_reconocimiento(self):
        """Envía la señal para detener el hilo de reconocimiento."""
        if self.stop_event:
            self.stop_event.set()
        # La UI se actualizará a través de la función de callback `_finalizar_reconocimiento_ui`

    def _actualizar_ui_para_reconocimiento(self, iniciado: bool):
        """Habilita/deshabilita botones y muestra/oculta el botón de detener."""
        if iniciado:
            self.btn_registrar.config(state='disabled')
            self.btn_entrenar.config(state='disabled')
            self.btn_reconocer_entrada.config(state='disabled')
            self.btn_reconocer_salida.config(state='disabled')
            self.btn_admin.config(state='disabled')
            self.btn_detener.pack(pady=10, ipady=5)
        else:
            self.btn_registrar.config(state='normal')
            self.btn_entrenar.config(state='normal')
            self.btn_reconocer_entrada.config(state='normal')
            self.btn_reconocer_salida.config(state='normal')
            self.btn_admin.config(state='normal')
            self.btn_detener.pack_forget()

    def _finalizar_reconocimiento_ui(self):
        """
        Callback para ser llamado desde el hilo de reconocimiento
        cuando este finaliza, para actualizar la UI.
        """
        # Tkinter no es seguro para hilos, por lo que usamos `after` para
        # programar la actualización de la UI en el hilo principal.
        self.root.after(0, self._actualizar_ui_para_reconocimiento, False)
        self.root.after(100, self._cargar_reporte) # Actualizar el reporte
        # También actualizamos la lista de personas por si se ha añadido alguien
        self.root.after(100, self._cargar_personas_registradas)

    def _cargar_reporte(self):
        """Carga los datos de la base de datos en la tabla del reporte, filtrando por el rango de fechas seleccionado."""
        # Limpiar tabla anterior
        for i in self.report_tree.get_children():
            self.report_tree.delete(i)

        # Obtener las fechas de los widgets DateEntry
        fecha_inicio = self.fecha_inicio_entry.get_date()
        fecha_fin = self.fecha_fin_entry.get_date()

        # Obtener y mostrar nuevos datos, pasando el rango de fechas a la función de la base de datos
        reporte = database.obtener_reporte_asistencia(fecha_inicio, fecha_fin)
        for i, registro in enumerate(reporte):
            # Asegurarse de que los valores nulos se muestren como vacíos
            hora_salida = registro['hora_salida'] if registro['hora_salida'] else ''
            horas_asistidas = registro['horas_asistidas'] if registro['horas_asistidas'] else ''
            
            # Asignar etiqueta para color de fila alternado
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'

            self.report_tree.insert('', 'end', values=(
                registro['persona_id'], 
                registro['nombre_completo'], 
                registro['fecha'], 
                registro['hora_entrada'], 
                hora_salida,
                horas_asistidas
            ), tags=(tag,))

    def _exportar_csv(self):
        """Exporta los datos actuales del Treeview a un archivo CSV."""
        # Pedir al usuario que elija la ubicación y el nombre del archivo
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            title="Guardar reporte como...",
            initialfile=f"reporte_asistencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if not filepath: # Si el usuario cancela el diálogo
            return

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([self.report_tree.heading(c)['text'] for c in self.report_tree['columns']]) # Escribir encabezados
            for child in self.report_tree.get_children():
                writer.writerow(self.report_tree.item(child)['values'])
        messagebox.showinfo("Exportación Exitosa", f"Reporte guardado como:\n{os.path.basename(filepath)}")

    def _create_personas_tab(self, tab):
        """Crea los widgets para la pestaña de personas registradas."""
        # --- Frame para controles ---
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill='x', pady=(0, 10))

        btn_actualizar = ttk.Button(control_frame, text="Actualizar Lista", command=self._cargar_personas_registradas)
        btn_actualizar.pack(side='left')

        btn_eliminar = ttk.Button(control_frame, text="Eliminar Persona Seleccionada", command=self._eliminar_persona, style='Stop.TButton')
        btn_eliminar.pack(side='left', padx=10)

        # --- Frame para la tabla y el scrollbar ---
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(expand=True, fill='both')

        # --- Treeview para la tabla ---
        columnas = ('id', 'nombre', 'fecha_registro')
        self.personas_tree = ttk.Treeview(tree_frame, columns=columnas, show='headings')

        self.personas_tree.tag_configure('oddrow', background='#f0f2f5')
        self.personas_tree.tag_configure('evenrow', background='#ffffff')

        self.personas_tree.heading('id', text='ID')
        self.personas_tree.heading('nombre', text='Nombre Completo')
        self.personas_tree.heading('fecha_registro', text='Fecha de Registro')

        self.personas_tree.column('id', width=80, anchor='center')
        self.personas_tree.column('nombre', width=300)
        self.personas_tree.column('fecha_registro', width=150, anchor='center')

        self.personas_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.personas_tree.yview)
        self.personas_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self._cargar_personas_registradas()

    def _cargar_personas_registradas(self):
        """Carga la lista de personas desde la BD al Treeview."""
        for i in self.personas_tree.get_children():
            self.personas_tree.delete(i)

        personas = database.obtener_todas_las_personas()
        for i, persona in enumerate(personas):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.personas_tree.insert('', 'end', values=(
                persona['id'],
                persona['nombre_completo'],
                persona['fecha_registro'].strftime('%Y-%m-%d %H:%M:%S')
            ), tags=(tag,))

    def _eliminar_persona(self):
        """Elimina una persona de la base de datos y sus fotos."""
        seleccion = self.personas_tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor, seleccione una persona para eliminar.", parent=self.root)
            return

        item = self.personas_tree.item(seleccion[0])
        persona_id = item['values'][0]
        nombre_persona = item['values'][1]

        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar a '{nombre_persona}' (ID: {persona_id})?\n\n¡ADVERTENCIA! Esta acción no se puede deshacer y eliminará todas las fotos de entrenamiento asociadas.", parent=self.root):
            # Eliminar la carpeta de datos de la persona
            person_path = os.path.join(DATA_PATH, str(persona_id))
            if os.path.exists(person_path):
                shutil.rmtree(person_path)

            # Eliminar a la persona de la base de datos
            if database.eliminar_persona_y_asistencia(persona_id):
                messagebox.showinfo("Éxito", f"'{nombre_persona}' ha sido eliminado.\n\nPor favor, vuelva a entrenar el modelo para aplicar los cambios.", parent=self.root)
                self._cargar_personas_registradas()
            else:
                messagebox.showerror("Error", "No se pudo eliminar a la persona de la base de datos.", parent=self.root)

if __name__ == "__main__":
    # Crear la carpeta 'data' si no existe
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
    
    # 0. Inicializar la base de datos (crear tablas, insertar usuario de prueba si es necesario)
    if not database.init_db():
        sys.exit(1) # Salir si la inicialización de la BD falla

    # 1. Crear la ventana raíz de Tkinter
    root = tk.Tk()
    # 2. Ocultarla inicialmente, ya que primero mostraremos el login
    root.withdraw() 
    def mostrar_app_principal():
        """
        Función callback que se ejecuta tras un login exitoso.
        Muestra la ventana principal y la inicializa.
        """
        login_window.destroy() # Asegurarse de que la ventana de login se cierre
        root.deiconify() # Hace visible la ventana principal
        app = App(root)
    # 3. Crear y mostrar la ventana de login. Le pasamos la función de callback.
    #    La creamos como una Toplevel independiente para asegurar que sea visible.
    login_window = tk.Toplevel(root)
    VentanaLogin(login_window, root, mostrar_app_principal) # Pasar 'root' como la ventana principal
    
    # 4. Iniciar el bucle principal de la aplicación
    root.mainloop()
