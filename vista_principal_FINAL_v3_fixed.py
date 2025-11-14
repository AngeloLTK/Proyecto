"""
Vista Principal - Interfaz Gráfica del Juego RPG (UNA SOLA VENTANA)
Proyecto Ingeniería de Software - Grupo 6
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from modelo_completo import *
import json
import os
import sys


# ========================================================================
# CONFIGURACIÓN DPI PARA WINDOWS (evita que se vea borroso o pequeño)
# ========================================================================
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)  # Para Windows 8.1+
except:
    try:
        windll.user32.SetProcessDPIAware()  # Para Windows Vista/7/8
    except:
        pass  # Si falla, continuar sin configuración DPI

# ========================================================================
# FUNCIÓN PARA PYINSTALLER - RUTAS DE RECURSOS
# ========================================================================
def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller"""
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class JuegoRPG:
    """Controlador principal - TODO en una sola ventana"""
    
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Juego RPG - A COMBATIR!")
        
        # ⭐ RESPONSIVE: Adaptar al tamaño de pantalla
        ancho_pantalla = self.ventana.winfo_screenwidth()
        alto_pantalla = self.ventana.winfo_screenheight()
        
        # Usar el 85% del tamaño de pantalla
        ancho_ventana = int(ancho_pantalla * 0.85)
        alto_ventana = int(alto_pantalla * 0.85)
        
        # Centrar la ventana
        pos_x = (ancho_pantalla - ancho_ventana) // 2
        pos_y = (alto_pantalla - alto_ventana) // 2
        
        self.ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{pos_x}+{pos_y}")
        self.ventana.configure(bg="#1a5490")
        self.ventana.resizable(True, True)  # Permitir redimensionar
        
        # ⭐ Soporte para pantalla completa con F11
        self.pantalla_completa = False
        self.ventana.bind("<F11>", self.toggle_pantalla_completa)
        self.ventana.bind("<Escape>", self.salir_pantalla_completa)
        
        # Variables del juego
        self.personaje = None
        self.historial = None
        self.combate_actual = None
        self.enemigo_actual = None
        self.imagen_tk = None
        self.gif_frames_jugador = []  # GIF del jugador
        self.gif_frames_enemigo = []  # GIF del enemigo
        
        # Contenedor principal que se reutiliza
        self.contenedor = tk.Frame(self.ventana, bg="#1a5490")
        self.contenedor.pack(fill="both", expand=True)
        
        # Mostrar pantalla de inicio
        self.mostrar_pantalla_inicio()
    
    def limpiar_contenedor(self):
        """Limpia el contenedor principal"""
        for widget in self.contenedor.winfo_children():
            widget.destroy()
    
    def toggle_pantalla_completa(self, event=None):
        """Alterna entre pantalla completa y ventana normal (F11)"""
        self.pantalla_completa = not self.pantalla_completa
        self.ventana.attributes("-fullscreen", self.pantalla_completa)
        return "break"
    
    def salir_pantalla_completa(self, event=None):
        """Sale de pantalla completa (ESC)"""
        self.pantalla_completa = False
        self.ventana.attributes("-fullscreen", False)
        return "break"
    
    # ========================================================================
    # PANTALLA 1: INICIO
    # ========================================================================
    
    def mostrar_pantalla_inicio(self):
        """Pantalla de creación de personaje"""
        self.limpiar_contenedor()
        
        # ⭐ IMAGEN DE FONDO - SIN RECORTAR, AJUSTAR Y LLENAR
        # Buscar la imagen fondo1 con diferentes extensiones
        posibles_fondos = ["fondo1.jpg", "fondo1.png", "fondo1.jpeg", "fondo1.gif"]
        fondo_encontrado = None
        
        for nombre_fondo in posibles_fondos:
            ruta_fondo = resource_path(nombre_fondo)
            if os.path.exists(ruta_fondo):
                fondo_encontrado = ruta_fondo
                break
        
        if fondo_encontrado:
            try:
                from PIL import Image, ImageTk
                # Forzar actualización de la ventana para obtener tamaño real
                self.ventana.update_idletasks()
                
                # Obtener tamaño de la VENTANA
                ancho_ventana = self.ventana.winfo_width()
                alto_ventana = self.ventana.winfo_height()
                
                # Si el tamaño es muy pequeño, usar valores por defecto
                if ancho_ventana < 100:
                    ancho_ventana = 1200
                    alto_ventana = 800
                
                # Cargar imagen de fondo
                img_fondo = Image.open(fondo_encontrado)
                
                # ⭐ REDIMENSIONAR SIN RECORTAR - mantener toda la imagen visible
                # Simplemente ajustar al tamaño exacto de la ventana (puede distorsionar ligeramente)
                img_fondo = img_fondo.resize((ancho_ventana, alto_ventana), Image.Resampling.LANCZOS)
                
                self.imagen_fondo = ImageTk.PhotoImage(img_fondo)
                
                # Crear label con la imagen de fondo que cubra TODO
                label_fondo = tk.Label(self.contenedor, image=self.imagen_fondo, bg="#1a5490")
                label_fondo.place(x=0, y=0, relwidth=1, relheight=1)
                label_fondo.image = self.imagen_fondo  # Mantener referencia
            except Exception as e:
                print(f"Error cargando fondo: {e}")
        
        # Frame principal centrado con borde
        frame = tk.Frame(self.contenedor, bg="#1a5490", relief="raised", bd=3)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # ⭐ GIF DEL CLÉRIGO ARRIBA (HORIZONTAL Y GRANDE)
        frame_gif = tk.Frame(frame, bg="#1a5490")
        frame_gif.pack(pady=(10, 10))  # Arriba del título
        
        label_gif = tk.Label(frame_gif, bg="#1a5490")
        label_gif.pack()
        
        # Cargar GIF del clérigo (MÁS GRANDE Y HORIZONTAL) - USAR resource_path
        clerigo_path = resource_path("clerigo.gif")
        if os.path.exists(clerigo_path):
            try:
                from PIL import Image, ImageTk
                self.gif_frames_inicio = []
                gif = Image.open(clerigo_path)
                
                try:
                    frame_count = 0
                    while True:
                        gif_frame = gif.copy()
                        
                        # Convertir a RGBA si no lo es
                        if gif_frame.mode != 'RGBA':
                            gif_frame = gif_frame.convert('RGBA')
                        
                        # Redimensionar MÁS GRANDE Y HORIZONTAL: 280x200 (más ancho que alto)
                        gif_frame = gif_frame.resize((280, 200), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(gif_frame)
                        self.gif_frames_inicio.append(photo)
                        frame_count += 1
                        gif.seek(frame_count)
                except EOFError:
                    pass
                
                if self.gif_frames_inicio:
                    # Función de animación mejorada
                    def animar_inicio(indice=0):
                        if hasattr(self, 'gif_frames_inicio') and self.gif_frames_inicio and label_gif.winfo_exists():
                            frame = self.gif_frames_inicio[indice]
                            label_gif.config(image=frame)
                            label_gif.image = frame  # Mantener referencia
                            siguiente = (indice + 1) % len(self.gif_frames_inicio)
                            label_gif.after(100, lambda: animar_inicio(siguiente))
                    
                    # Iniciar animación
                    animar_inicio()
                else:
                    label_gif.config(text="⚔️", font=("Arial", 60), fg="white")
            except Exception as e:
                print(f"Error cargando GIF: {e}")
                label_gif.config(text="⚔️", font=("Arial", 60), fg="white")
        else:
            label_gif.config(text="⚔️", font=("Arial", 60), fg="white")
        
        # TÍTULO DEBAJO DEL GIF
        tk.Label(
            frame, text="Juego RPG\nA COMBATIR!",
            font=("Arial", 48, "bold"), fg="white", bg="#1a5490"
        ).pack(pady=20)
        
        # NOMBRE (más grande)
        tk.Label(
            frame, text="Ingrese su nombre:",
            font=("Arial", 18), fg="white", bg="#1a5490"
        ).pack(pady=5)
        
        self.entrada_nombre = tk.Entry(frame, font=("Arial", 18), width=20, justify="center")
        self.entrada_nombre.pack(pady=10)
        self.entrada_nombre.focus()
        
        # SELECCIONE SU CLASE (más grande)
        tk.Label(
            frame, text="Seleccione su clase:",
            font=("Arial", 18), fg="white", bg="#1a5490"
        ).pack(pady=(30, 10))
        
        frame_clases = tk.Frame(frame, bg="#1a5490")
        frame_clases.pack(pady=10)
        
        clases = [
            ("Guerrero", "⚔️", Guerrero),
            ("Mago", "🔮", Mago),
            ("Clérigo", "✨", Clerigo),
            ("Luchador", "👊", Luchador)
        ]
        
        # BOTONES DE CLASE MÁS GRANDES
        for i, (nombre, emoji, clase) in enumerate(clases):
            tk.Button(
                frame_clases, text=f"{emoji}\n{nombre}",
                font=("Arial", 16, "bold"), width=14, height=4,
                command=lambda c=clase: self.crear_personaje(c),
                bg="#2a6ab0", fg="white", cursor="hand2"
            ).grid(row=0, column=i, padx=8)
        
        self.entrada_nombre.bind("<Return>", lambda e: self.crear_personaje(Guerrero))
    
    def crear_personaje(self, ClasePersonaje):
        """Crea el personaje"""
        nombre = self.entrada_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Error", "Ingresa un nombre")
            return
        
        self.personaje = ClasePersonaje(nombre)
        self.historial = Historial(self.personaje)
        self.mostrar_menu_principal()
    
    # ========================================================================
    # PANTALLA 2: MENÚ PRINCIPAL
    # ========================================================================
    
    def mostrar_menu_principal(self):
        """Menú principal con stats y opciones"""
        self.limpiar_contenedor()
        
        # ⭐ IMAGEN DE FONDO
        posibles_fondos = ["fondo1.jpg", "fondo1.png", "fondo1.jpeg", "fondo1.gif"]
        fondo_encontrado = None
        
        for nombre_fondo in posibles_fondos:
            ruta_fondo = resource_path(nombre_fondo)
            if os.path.exists(ruta_fondo):
                fondo_encontrado = ruta_fondo
                break
        
        if fondo_encontrado:
            try:
                from PIL import Image, ImageTk
                self.ventana.update_idletasks()
                
                ancho_ventana = self.ventana.winfo_width()
                alto_ventana = self.ventana.winfo_height()
                
                if ancho_ventana < 100:
                    ancho_ventana = 1200
                    alto_ventana = 800
                
                img_fondo = Image.open(fondo_encontrado)
                img_fondo = img_fondo.resize((ancho_ventana, alto_ventana), Image.Resampling.LANCZOS)
                self.imagen_fondo_menu = ImageTk.PhotoImage(img_fondo)
                
                label_fondo = tk.Label(self.contenedor, image=self.imagen_fondo_menu, bg="#1a5490")
                label_fondo.place(x=0, y=0, relwidth=1, relheight=1)
                label_fondo.image = self.imagen_fondo_menu
            except Exception as e:
                print(f"Error cargando fondo en menú: {e}")
        
        # Header
        tk.Label(
            self.contenedor,
            text=f"🎮 {self.personaje.nombre} - {self.personaje.evolucion_actual}",
            font=("Arial", 20, "bold"), fg="white", bg="#1a5490"
        ).pack(pady=15)
        
        # Contenedor de 2 columnas
        frame_principal = tk.Frame(self.contenedor, bg="#1a5490")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=10)
        
        # IZQUIERDA: Estadísticas
        panel_stats = tk.Frame(frame_principal, bg="#2a6ab0", relief="raised", bd=3)
        panel_stats.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(
            panel_stats, text="📊 Estadísticas",
            font=("Arial", 20, "bold"), fg="white", bg="#2a6ab0"
        ).pack(pady=10)
        
        # Frame para imagen (más grande)
        frame_img = tk.Frame(panel_stats, bg="white", width=220, height=220)
        frame_img.pack(pady=10)
        frame_img.pack_propagate(False)
        
        # Cargar y mostrar imagen si existe - USAR resource_path
        if self.personaje.imagen_path:
            imagen_path = resource_path(self.personaje.imagen_path) if not os.path.isabs(self.personaje.imagen_path) else self.personaje.imagen_path
            if os.path.exists(imagen_path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(imagen_path)
                    img = img.resize((210, 210), Image.Resampling.LANCZOS)  # ← AUMENTADO de 140 a 210
                    self.imagen_tk = ImageTk.PhotoImage(img)  # Guardar referencia
                    tk.Label(frame_img, image=self.imagen_tk, bg="white").pack(expand=True)
                except Exception as e:
                    # Si falla, mostrar placeholder
                    tk.Label(frame_img, text="🎭\nImagen del\nPersonaje", font=("Arial", 14), bg="white").pack(expand=True)
            else:
                tk.Label(frame_img, text="🎭\nImagen del\nPersonaje", font=("Arial", 14), bg="white").pack(expand=True)
        else:
            tk.Label(frame_img, text="🎭\nImagen del\nPersonaje", font=("Arial", 14), bg="white").pack(expand=True)
        
        # Botón para cargar imagen
        tk.Button(
            panel_stats, text="📷 Cargar Imagen",
            font=("Arial", 11), command=self.cargar_imagen,
            bg="#1a5490", fg="white", cursor="hand2"
        ).pack(pady=5)
        
        # Stats
        info = self.personaje.obtener_info()
        stats_frame = tk.Frame(panel_stats, bg="#2a6ab0")
        stats_frame.pack(pady=20, padx=20)
        
        stats = [
            ("Nivel:", info['nivel']),
            ("HP:", f"{info['hp']}/{info['hp_maximo']}"),
            ("Dinero:", f"${info['dinero']}"),
            ("", "")
        ]
        
        if self.personaje._usa_fuerza:
            stats.append(("Fuerza:", info['fuerza']))
        else:
            stats.append(("Inteligencia:", info['inteligencia']))
        
        stats.extend([
            ("Agilidad:", info['agilidad']),
            ("Vitalidad:", info['vitalidad'])
        ])
        
        for i, (nombre, valor) in enumerate(stats):
            if nombre:
                tk.Label(
                    stats_frame, text=nombre, font=("Arial", 20, "bold"),  # ← AUMENTADO de 12 a 14
                    fg="white", bg="#2a6ab0", anchor="w"
                ).grid(row=i, column=0, sticky="w", pady=3)
                tk.Label(
                    stats_frame, text=str(valor), font=("Arial", 20),  # ← AUMENTADO de 12 a 14
                    fg="yellow", bg="#2a6ab0", anchor="e"
                ).grid(row=i, column=1, sticky="e", pady=3, padx=(10, 0))
        
        # DERECHA: Acciones
        panel_acciones = tk.Frame(frame_principal, bg="#2a6ab0", relief="raised", bd=3)
        panel_acciones.pack(side="right", fill="both", expand=True)
        
        tk.Label(
            panel_acciones, text="⚡ Acciones",
            font=("Arial", 20, "bold"), fg="white", bg="#2a6ab0"
        ).pack(pady=20)
        
        # Solo botones esenciales del menú principal
        botones = [
            ("⚔️ COMBATIR", self.preparar_combate, "#28a745"),
            ("💊 SANAR ($20)", self.sanar_personaje, "#007bff"),
            ("📊 MI HISTORIAL", self.ver_historial, "#6f42c1"),
            ("👥 RETIRADOS", self.ver_personajes_retirados, "#17a2b8"),
            ("🚪 RETIRAR", self.retirar_personaje, "#fd7e14"),
            ("❌ SALIR", self.salir_juego, "#dc3545")
        ]
        
        for texto, comando, color in botones:
            tk.Button(
                panel_acciones, text=texto, font=("Arial", 16, "bold"),
                command=comando, width=20, height=3, cursor="hand2",  # ← AUMENTADO de height=2 a height=3
                bg=color, fg="white"
            ).pack(pady=15)
    
    # ========================================================================
    # PANTALLA 3: COMBATE (INTERACTIVO TURNO POR TURNO)
    # ========================================================================
    
    def cargar_imagen(self):
        """Permite cargar una imagen para el personaje"""
        import os
        archivo = filedialog.askopenfilename(
            title="Seleccionar imagen del personaje",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Todos", "*.*")
            ]
        )
        if archivo:
            # Verificar que el archivo existe
            if os.path.exists(archivo):
                self.personaje.imagen_path = archivo
                messagebox.showinfo("✓ Imagen cargada", "La imagen se cargó correctamente")
                self.mostrar_menu_principal()
            else:
                messagebox.showerror("Error", "No se pudo cargar la imagen")
    
    def preparar_combate(self):
        """Prepara el combate"""
        if self.personaje.hp <= 0:
            messagebox.showerror("Error", "No puedes combatir con 0 HP. Debes sanarte primero.")
            return
        
        # Generar enemigo
        self.enemigo_actual = GeneradorEnemigos.generar_enemigo(self.personaje.nivel)
        self.combate_actual = Combate(self.personaje, self.enemigo_actual)
        
        # Mostrar pantalla de combate
        self.mostrar_pantalla_combate()
    
    def mostrar_pantalla_combate(self):
        """Muestra la pantalla de combate con layout mejorado"""
        self.limpiar_contenedor()
        
        # ⭐ IMAGEN DE FONDO - IGUAL QUE EN INICIO
        posibles_fondos = ["fondo1.jpg", "fondo1.png", "fondo1.jpeg", "fondo1.gif"]
        fondo_encontrado = None
        
        for nombre_fondo in posibles_fondos:
            ruta_fondo = resource_path(nombre_fondo)
            if os.path.exists(ruta_fondo):
                fondo_encontrado = ruta_fondo
                break
        
        if fondo_encontrado:
            try:
                from PIL import Image, ImageTk
                self.ventana.update_idletasks()
                
                ancho_ventana = self.ventana.winfo_width()
                alto_ventana = self.ventana.winfo_height()
                
                if ancho_ventana < 100:
                    ancho_ventana = 1200
                    alto_ventana = 800
                
                img_fondo = Image.open(fondo_encontrado)
                img_fondo = img_fondo.resize((ancho_ventana, alto_ventana), Image.Resampling.LANCZOS)
                self.imagen_fondo_combate = ImageTk.PhotoImage(img_fondo)
                
                label_fondo = tk.Label(self.contenedor, image=self.imagen_fondo_combate, bg="#1a5490")
                label_fondo.place(x=0, y=0, relwidth=1, relheight=1)
                label_fondo.image = self.imagen_fondo_combate
            except Exception as e:
                print(f"Error cargando fondo en combate: {e}")
        
        # ===== HEADER =====
        tk.Label(
            self.contenedor, text="⚔️ ¡COMBATE!",
            font=("Arial", 24, "bold"), fg="white", bg="#1a5490"
        ).pack(pady=10)
        
        # ===== SECCIÓN SUPERIOR: PERSONAJES LADO A LADO =====
        frame_personajes = tk.Frame(self.contenedor, bg="#1a5490")
        frame_personajes.pack(pady=10, padx=20, fill="x")
        
        # JUGADOR (IZQUIERDA)
        frame_jugador = tk.Frame(frame_personajes, bg="#2a6ab0", relief="raised", bd=3)
        frame_jugador.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # NOMBRE MÁS GRANDE
        tk.Label(
            frame_jugador, text=f"👤 {self.personaje.nombre}",
            font=("Arial", 18, "bold"), fg="white", bg="#2a6ab0"  # ← AUMENTADO de 14 a 18
        ).pack(pady=5)
        
        # CLASE Y NIVEL MÁS GRANDE
        tk.Label(
            frame_jugador, 
            text=f"{self.personaje.evolucion_actual} | Nivel {self.personaje.nivel}",
            font=("Courier", 14), fg="lightgray", bg="#2a6ab0"  # ← AUMENTADO de 11 a 14
        ).pack()
        
        # Stats del jugador (se actualizan) - HP MÁS GRANDE
        self.label_hp_jugador = tk.Label(
            frame_jugador, 
            text=f"❤️ HP: {self.personaje.hp}/{self.personaje.vitalidad // 2}",
            font=("Arial", 20, "bold"), fg="yellow", bg="#2a6ab0"  # ← AUMENTADO de 16 a 20
        )
        self.label_hp_jugador.pack(pady=10)
        
        # Barra de HP jugador (MÁS GRANDE)
        self.canvas_hp_jugador = tk.Canvas(frame_jugador, width=250, height=25, bg="#1a5490", highlightthickness=0)  # ← AUMENTADO de 200x20 a 250x25
        self.canvas_hp_jugador.pack(pady=5)
        self.actualizar_barra_hp(self.canvas_hp_jugador, self.personaje)
        
        # GIF DEL JUGADOR (MÁS GRANDE)
        self.label_gif_jugador = tk.Label(frame_jugador, bg="#2a6ab0")
        self.label_gif_jugador.pack(pady=10)
        self.cargar_gif_personaje(self.personaje, self.label_gif_jugador, es_jugador=True)
        
        # VS en el centro
        tk.Label(
            frame_personajes, text="⚔️\nVS",
            font=("Arial", 16, "bold"), fg="yellow", bg="#1a5490"
        ).pack(side="left", padx=10)
        
        # ENEMIGO (DERECHA)
        frame_enemigo = tk.Frame(frame_personajes, bg="#6a2a2a", relief="raised", bd=3)
        frame_enemigo.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # NOMBRE MÁS GRANDE
        tk.Label(
            frame_enemigo, text=f"💀 {self.enemigo_actual.nombre}",
            font=("Arial", 18, "bold"), fg="white", bg="#6a2a2a"  # ← AUMENTADO de 14 a 18
        ).pack(pady=5)
        
        # CLASE Y NIVEL MÁS GRANDE
        tk.Label(
            frame_enemigo,
            text=f"{self.enemigo_actual.evolucion_actual} | Nivel {self.enemigo_actual.nivel}",
            font=("Courier", 14), fg="lightgray", bg="#6a2a2a"  # ← AUMENTADO de 11 a 14
        ).pack()
        
        # Stats del enemigo (se actualizan) - HP MÁS GRANDE
        self.label_hp_enemigo = tk.Label(
            frame_enemigo,
            text=f"❤️ HP: {self.enemigo_actual.hp}/{self.enemigo_actual.vitalidad // 2}",
            font=("Arial", 20, "bold"), fg="orange", bg="#6a2a2a"  # ← AUMENTADO de 16 a 20
        )
        self.label_hp_enemigo.pack(pady=10)
        
        # Barra de HP enemigo (MÁS GRANDE)
        self.canvas_hp_enemigo = tk.Canvas(frame_enemigo, width=250, height=25, bg="#3a1a1a", highlightthickness=0)  # ← AUMENTADO de 200x20 a 250x25
        self.canvas_hp_enemigo.pack(pady=5)
        self.actualizar_barra_hp(self.canvas_hp_enemigo, self.enemigo_actual)
        
        # GIF DEL ENEMIGO (MÁS GRANDE)
        self.label_gif_enemigo = tk.Label(frame_enemigo, bg="#6a2a2a")
        self.label_gif_enemigo.pack(pady=10)
        self.cargar_gif_personaje(self.enemigo_actual, self.label_gif_enemigo, es_jugador=False)
        
        # ===== SECCIÓN MEDIA: LOG DE COMBATE =====
        tk.Label(
            self.contenedor, text="📜 Log de Combate",
            font=("Arial", 14, "bold"), fg="white", bg="#1a5490"
        ).pack(pady=(10, 5))
        
        log_frame = tk.Frame(self.contenedor, bg="white", relief="sunken", bd=2)
        log_frame.pack(pady=5, padx=30, fill="both", expand=False)  # expand=False
        
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.log_text = tk.Text(
            log_frame, 
            font=("Consolas", 16),
            yscrollcommand=scrollbar.set, 
            wrap="word",
            state="disabled", 
            bg="#f8f9fa", 
            height=6,  # Reducido de 8 a 6 líneas
            padx=10,
            pady=8
        )
        self.log_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # ⭐ Configurar tags para centrado y formato
        self.log_text.tag_configure("centrado", justify="center", font=("Arial", 16, "bold"))
        self.log_text.tag_configure("normal", justify="left", font=("Consolas", 15))
        
        # Mensaje inicial
        if not self.combate_actual.combate_iniciado:
            self.agregar_al_log(self.combate_actual.obtener_mensaje_inicial())
            self.agregar_al_log("")
            self.combate_actual.combate_iniciado = True
        
        # ===== SECCIÓN INFERIOR: CONTROLES (4 BOTONES ESTILO POKÉMON) =====
        frame_controles = tk.Frame(self.contenedor, bg="#1a5490")
        frame_controles.pack(pady=10)
        
        # Label de turno actual
        self.label_turno = tk.Label(
            frame_controles,
            text=f"Turno {self.combate_actual.turno_actual}",
            font=("Arial", 13, "bold"), fg="yellow", bg="#1a5490"
        )
        self.label_turno.pack(pady=8)
        
        # Grid 2x2 de botones (estilo Pokémon)
        frame_botones = tk.Frame(frame_controles, bg="#1a5490")
        frame_botones.pack(pady=5)
        
        # COMBATIR (ejecutar turno)
        self.btn_combatir = tk.Button(
            frame_botones,
            text="⚔️ COMBATIR",
            font=("Arial", 15, "bold"),  # ← AUMENTADO de 13 a 15
            width=20, height=3,  # ← AUMENTADO de height=2 a height=3
            bg="#28a745", fg="white",
            command=self.ejecutar_siguiente_turno,
            cursor="hand2"
        )
        self.btn_combatir.grid(row=0, column=0, padx=8, pady=8)
        
        # SANAR
        self.btn_sanar = tk.Button(
            frame_botones,
            text="💊 SANAR\n(Cuesta $20)",
            font=("Arial", 15, "bold"),  # ← AUMENTADO de 13 a 15
            width=20, height=3,  # ← AUMENTADO de height=2 a height=3
            bg="#007bff", fg="white",
            command=self.sanar_en_combate,
            cursor="hand2"
        )
        self.btn_sanar.grid(row=0, column=1, padx=8, pady=8)
        
        # VER STATS
        self.btn_stats = tk.Button(
            frame_botones,
            text="📊 VER STATS",
            font=("Arial", 15, "bold"),  # ← AUMENTADO de 13 a 15
            width=20, height=3,  # ← AUMENTADO de height=2 a height=3
            bg="#6f42c1", fg="white",
            command=self.ver_historial,
            cursor="hand2"
        )
        self.btn_stats.grid(row=1, column=0, padx=8, pady=8)
        
        # HUIR/RETIRAR
        self.btn_huir = tk.Button(
            frame_botones,
            text="🏃 HUIR",
            font=("Arial", 15, "bold"),  # ← AUMENTADO de 13 a 15
            width=20, height=3,  # ← AUMENTADO de height=2 a height=3
            bg="#dc3545", fg="white",
            command=self.huir_combate,
            cursor="hand2"
        )
        self.btn_huir.grid(row=1, column=1, padx=8, pady=8)
    
    def actualizar_barra_hp(self, canvas, personaje):
        """Actualiza la barra visual de HP"""
        canvas.delete("all")
        hp_max = personaje.vitalidad // 2
        hp_actual = personaje.hp
        porcentaje = hp_actual / hp_max if hp_max > 0 else 0
        
        # Obtener tamaño del canvas
        ancho = int(canvas.cget("width"))
        alto = int(canvas.cget("height"))
        
        # Borde
        canvas.create_rectangle(2, 2, ancho-2, alto-2, outline="black", width=2)
        
        # Barra de HP
        ancho_barra = int((ancho - 8) * porcentaje)
        
        # Color según porcentaje
        if porcentaje > 0.5:
            color = "#28a745"  # Verde
        elif porcentaje > 0.25:
            color = "#ffc107"  # Amarillo
        else:
            color = "#dc3545"  # Rojo
        
        if ancho_barra > 0:
            canvas.create_rectangle(4, 4, 4 + ancho_barra, alto-4, fill=color, outline="")
    
    def actualizar_stats_combate(self):
        """Actualiza las estadísticas visuales durante el combate"""
        # Actualizar labels de HP
        self.label_hp_jugador.config(
            text=f"❤️ HP: {self.personaje.hp}/{self.personaje.vitalidad // 2}"
        )
        self.label_hp_enemigo.config(
            text=f"❤️ HP: {self.enemigo_actual.hp}/{self.enemigo_actual.vitalidad // 2}"
        )
        
        # Actualizar barras
        self.actualizar_barra_hp(self.canvas_hp_jugador, self.personaje)
        self.actualizar_barra_hp(self.canvas_hp_enemigo, self.enemigo_actual)
        
        # Actualizar número de turno
        self.label_turno.config(text=f"Turno {self.combate_actual.turno_actual}")
    
    def agregar_al_log(self, mensaje):
        """Agrega mensaje al log de combate con iconos y formato mejorado"""
        self.log_text.config(state="normal")
        
        # ⭐ Detectar tipo de mensaje y agregar iconos
        mensaje_formateado = mensaje
        tag = "normal"
        
        # Si es un título de turno (contiene "Turno" o "---")
        if "Turno" in mensaje or "---" in mensaje:
            # Extraer número de turno si existe
            if "Turno" in mensaje:
                import re
                match = re.search(r'Turno (\d+)', mensaje)
                if match:
                    num_turno = match.group(1)
                    mensaje_formateado = f"⚔️ ═══ TURNO {num_turno} ═══ ⚔️"
                else:
                    mensaje_formateado = mensaje
            tag = "centrado"
        
        # Reemplazar palabras clave con iconos
        elif "ataca" in mensaje.lower():
            mensaje_formateado = mensaje.replace("•", "⚔️")
            # Si no tiene viñeta, agregar icono al inicio
            if "⚔️" not in mensaje_formateado:
                mensaje_formateado = "  ⚔️ " + mensaje_formateado
        
        elif "daño" in mensaje.lower() or "hp" in mensaje.lower():
            if "⚔️" not in mensaje_formateado:
                mensaje_formateado = "  💥 " + mensaje
        
        elif "restante" in mensaje.lower():
            mensaje_formateado = mensaje.replace("•", "❤️")
            if "❤️" not in mensaje_formateado:
                mensaje_formateado = "  ❤️ " + mensaje
        
        elif "gana" in mensaje.lower() or "victoria" in mensaje.lower():
            mensaje_formateado = "  🏆 " + mensaje
            tag = "centrado"
        
        elif "pierde" in mensaje.lower() or "derrota" in mensaje.lower():
            mensaje_formateado = "  💀 " + mensaje
            tag = "centrado"
        
        elif "empieza" in mensaje.lower() or "combate" in mensaje.lower() and "!" in mensaje:
            mensaje_formateado = "⚔️ " + mensaje
            tag = "centrado"
        
        # Reemplazar viñetas genéricas
        mensaje_formateado = mensaje_formateado.replace("•", "▸")
        
        # Insertar el mensaje con el tag correspondiente
        inicio = self.log_text.index("end-1c")
        self.log_text.insert("end", mensaje_formateado + "\n")
        fin = self.log_text.index("end-1c")
        self.log_text.tag_add(tag, inicio, fin)
        
        self.log_text.see("end")
        self.log_text.config(state="disabled")
    
    def cargar_gif_personaje(self, personaje, label, es_jugador=True):
        """Carga el GIF animado del personaje - USAR resource_path"""
        # Mapeo de clases a archivos GIF
        mapeo_gifs = {
            "Guerrero": "imagen1.gif",
            "Mago": "imagen2.gif",
            "Clérigo": "imagen3.gif",
            "Luchador": "imagen4.gif"
        }
        
        archivo_gif = mapeo_gifs.get(personaje.clase, "imagen1.gif")
        archivo_gif_path = resource_path(archivo_gif)  # ← USAR resource_path
        
        if os.path.exists(archivo_gif_path):
            try:
                from PIL import Image, ImageTk
                # Lista de frames según si es jugador o enemigo
                frames = []
                gif = Image.open(archivo_gif_path)
                
                # Extraer todos los frames (MÁS GRANDES)
                try:
                    while True:
                        frame = gif.copy()
                        frame = frame.resize((160, 160), Image.Resampling.LANCZOS)  # ← AUMENTADO de 120 a 160
                        photo = ImageTk.PhotoImage(frame)
                        frames.append(photo)
                        gif.seek(len(frames))
                except EOFError:
                    pass
                
                # Guardar frames en la lista correspondiente
                if es_jugador:
                    self.gif_frames_jugador = frames
                else:
                    self.gif_frames_enemigo = frames
                
                # Iniciar animación
                if frames:
                    label.config(image=frames[0])
                    self.animar_gif(label, 0, es_jugador)
            except Exception as e:
                print(f"Error cargando GIF: {e}")
                # Si falla, mostrar placeholder
                label.config(text="🎮", font=("Arial", 50))  # ← AUMENTADO de 40 a 50
        else:
            # Si no existe el archivo, mostrar placeholder
            label.config(text="🎮", font=("Arial", 50))  # ← AUMENTADO de 40 a 50
    
    def animar_gif(self, label, frame_idx, es_jugador):
        """Anima el GIF frame por frame"""
        frames = self.gif_frames_jugador if es_jugador else self.gif_frames_enemigo
        
        if frames:
            label.config(image=frames[frame_idx])
            next_frame = (frame_idx + 1) % len(frames)
            label.after(100, self.animar_gif, label, next_frame, es_jugador)
    
    def mostrar_efecto_fight(self):
        """Muestra solo las letras FIGHT! sin fondo que tape"""
        # Crear label con texto sobre el contenido
        label_fight = tk.Label(
            self.ventana,
            text="FIGHT!",
            font=("Impact", 100, "bold"),
            fg="#FF4500",  # Naranja
            bg="#1a5490"   # Mismo color de fondo del juego para que se mezcle
        )
        label_fight.place(relx=0.5, rely=0.45, anchor="center")
        
        # Variables para la animación
        tamaño_inicial = 30
        tamaño_max = 100
        
        def animar_texto(tamaño, paso):
            if paso < 8:  # Crece
                nuevo_tamaño = tamaño + 10
                label_fight.config(font=("Impact", nuevo_tamaño, "bold"))
                label_fight.after(30, animar_texto, nuevo_tamaño, paso + 1)
            elif paso < 20:  # Se mantiene visible
                label_fight.after(40, animar_texto, tamaño, paso + 1)
            else:  # Desaparece
                label_fight.destroy()
        
        # Iniciar con texto pequeño
        label_fight.config(font=("Impact", tamaño_inicial, "bold"))
        animar_texto(tamaño_inicial, 0)
    
    def ejecutar_siguiente_turno(self):
        """Ejecuta el siguiente turno del combate"""
        # Mostrar efecto FIGHT!
        self.mostrar_efecto_fight()
        
        # Esperar un momento y luego ejecutar el turno
        self.contenedor.after(800, self._ejecutar_turno_real)
    
    def _ejecutar_turno_real(self):
        """Ejecuta realmente el turno después del efecto"""
        # Ejecutar turno completo
        continua, mensajes = self.combate_actual.ejecutar_turno_completo()
        
        # Mostrar mensajes
        for msg in mensajes:
            self.agregar_al_log(msg)
        
        # ACTUALIZAR STATS VISUALES
        self.actualizar_stats_combate()
        
        if not continua:
            # Combate terminado
            self.finalizar_combate_con_botones()
    
    def finalizar_combate_con_botones(self):
        """Finaliza combate y deshabilita/actualiza botones"""
        resultado = self.combate_actual.finalizar_combate()
        
        # Mostrar mensajes finales
        self.agregar_al_log("")
        for linea in resultado['log'][-2:]:
            self.agregar_al_log(linea)
        
        # Registrar en historial
        self.historial.registrar_combate(resultado)
        
        # Deshabilitar botón de combatir
        self.btn_combatir.config(
            text="✓ COMBATE\nTERMINADO",
            state="disabled",
            bg="#6c757d"
        )
        
        # Cambiar botón HUIR a CONTINUAR
        self.btn_huir.config(
            text="➡️ CONTINUAR",
            bg="#28a745",
            command=lambda: self.continuar_despues_combate(resultado)
        )
    
    def continuar_despues_combate(self, resultado):
        """Continúa después del combate"""
        if resultado['subio_nivel']:
            self.mostrar_distribucion_puntos()
        else:
            self.mostrar_menu_principal()
    
    def sanar_en_combate(self):
        """Sana durante el combate"""
        resultado = SistemaSanacion.sanar_personaje(self.personaje)
        
        if resultado['exito']:
            self.historial.registrar_sanacion(resultado)
            self.agregar_al_log(f"\n💊 {self.personaje.nombre} se sana y recupera {resultado['hp_recuperado']} HP")
            self.agregar_al_log(f"   Dinero restante: ${resultado['dinero_restante']}")
            
            # Actualizar stats visuales
            self.actualizar_stats_combate()
            
            messagebox.showinfo("✓ Sanación", resultado['mensaje'])
        else:
            messagebox.showwarning("✗ Error", resultado['mensaje'])
    
    def huir_combate(self):
        """Huye del combate (vuelve al menú)"""
        respuesta = messagebox.askyesno(
            "🏃 Huir del combate",
            "¿Deseas huir del combate?\n\nNo perderás HP ni dinero."
        )
        
        if respuesta:
            self.mostrar_menu_principal()
    
    def actualizar_info_combatientes(self):
        """DEPRECATED - ahora se usa actualizar_stats_combate()"""
        pass
    
    def finalizar_combate(self):
        """Finaliza el combate y muestra resultado"""
        resultado = self.combate_actual.finalizar_combate()
        
        # Mostrar mensajes finales
        self.agregar_al_log("")
        for linea in resultado['log'][-2:]:  # Últimas 2 líneas
            self.agregar_al_log(linea)
        
        # Registrar en historial
        self.historial.registrar_combate(resultado)
        
        # Ocultar botón de ejecutar turno
        self.btn_turno.pack_forget()
        
        # Mostrar opciones post-combate
        self.mostrar_opciones_post_combate(resultado)
    
    def mostrar_opciones_post_combate(self, resultado):
        """Muestra opciones después del combate (estilo Pokémon)"""
        # Frame de opciones
        frame_opciones = tk.Frame(self.contenedor, bg="#1a5490")
        frame_opciones.pack(pady=15)
        
        tk.Label(
            frame_opciones,
            text="¿Qué harás?",
            font=("Arial", 14, "bold"),
            fg="yellow",
            bg="#1a5490"
        ).pack(pady=10)
        
        # Grid de botones 2x2 (estilo Pokémon)
        frame_botones = tk.Frame(frame_opciones, bg="#1a5490")
        frame_botones.pack()
        
        # Determinar qué opciones mostrar según resultado
        if resultado['es_victoria']:
            # Si ganó, puede distribuir puntos primero si subió nivel
            if resultado['subio_nivel']:
                tk.Button(
                    frame_botones,
                    text="📈 DISTRIBUIR\nPUNTOS",
                    font=("Arial", 11, "bold"),
                    width=15, height=3,
                    bg="#ffc107", fg="black",
                    command=self.distribuir_y_continuar,
                    cursor="hand2"
                ).grid(row=0, column=0, padx=5, pady=5)
            else:
                tk.Button(
                    frame_botones,
                    text="⚔️ COMBATIR\nOTRA VEZ",
                    font=("Arial", 11, "bold"),
                    width=15, height=3,
                    bg="#28a745", fg="white",
                    command=self.preparar_combate,
                    cursor="hand2"
                ).grid(row=0, column=0, padx=5, pady=5)
        else:
            # Si perdió, no puede combatir hasta sanar
            if self.personaje.hp > 0:
                tk.Button(
                    frame_botones,
                    text="⚔️ COMBATIR\nOTRA VEZ",
                    font=("Arial", 11, "bold"),
                    width=15, height=3,
                    bg="#28a745", fg="white",
                    command=self.preparar_combate,
                    cursor="hand2"
                ).grid(row=0, column=0, padx=5, pady=5)
            else:
                tk.Button(
                    frame_botones,
                    text="❌ NO PUEDES\nCOMBATIR",
                    font=("Arial", 11, "bold"),
                    width=15, height=3,
                    bg="#6c757d", fg="white",
                    state="disabled"
                ).grid(row=0, column=0, padx=5, pady=5)
        
        tk.Button(
            frame_botones,
            text="💊 SANAR",
            font=("Arial", 11, "bold"),
            width=15, height=3,
            bg="#007bff", fg="white",
            command=self.sanar_desde_combate,
            cursor="hand2"
        ).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(
            frame_botones,
            text="📊 VER\nESTADÍSTICAS",
            font=("Arial", 11, "bold"),
            width=15, height=3,
            bg="#6f42c1", fg="white",
            command=self.ver_historial,
            cursor="hand2"
        ).grid(row=1, column=0, padx=5, pady=5)
        
        tk.Button(
            frame_botones,
            text="🏠 VOLVER AL\nMENÚ",
            font=("Arial", 11, "bold"),
            width=15, height=3,
            bg="#17a2b8", fg="white",
            command=self.mostrar_menu_principal,
            cursor="hand2"
        ).grid(row=1, column=1, padx=5, pady=5)
    
    def distribuir_y_continuar(self):
        """Distribuye puntos y luego muestra opciones"""
        self.mostrar_distribucion_puntos()
    
    def sanar_desde_combate(self):
        """Sana durante el flujo de combate"""
        resultado = SistemaSanacion.sanar_personaje(self.personaje)
        
        if resultado['exito']:
            self.historial.registrar_sanacion(resultado)
            messagebox.showinfo("✓ Sanación", resultado['mensaje'])
            # Volver a mostrar pantalla de combate preparada
            self.preparar_combate()
        else:
            messagebox.showwarning("✗ Error", resultado['mensaje'])
    
    # ========================================================================
    # PANTALLA 4: DISTRIBUCIÓN DE PUNTOS
    # ========================================================================
    
    def mostrar_distribucion_puntos(self):
        """Pantalla para distribuir puntos"""
        self.limpiar_contenedor()
        
        # ⭐ NUEVO: Verificar si puede evolucionar ANTES de distribuir puntos
        if self.personaje.puede_evolucionar():
            self.mostrar_pantalla_evolucion()
            return
        
        # ⭐ TÍTULO MÁS GRANDE (doble)
        tk.Label(
            self.contenedor,
            text=f"🎉 ¡Subiste al nivel {self.personaje.nivel}!",
            font=("Arial", 40, "bold"), fg="white", bg="#1a5490"  # ← 20 a 40
        ).pack(pady=50)  # ← 30 a 50
        
        # ⭐ SUBTÍTULO MÁS GRANDE (doble)
        tk.Label(
            self.contenedor, text="Distribuye 3 puntos entre tus atributos:",
            font=("Arial", 28), fg="white", bg="#1a5490"  # ← 14 a 28
        ).pack(pady=20)  # ← 10 a 20
        
        # Frame para sliders
        frame_sliders = tk.Frame(self.contenedor, bg="#1a5490")
        frame_sliders.pack(pady=40)  # ← 20 a 40
        
        if self.personaje._usa_fuerza:
            atributos = ["Fuerza", "Agilidad", "Vitalidad"]
        else:
            atributos = ["Inteligencia", "Agilidad", "Vitalidad"]
        
        self.sliders = {}
        self.labels_valor = {}
        
        for attr in atributos:
            frame_attr = tk.Frame(frame_sliders, bg="#1a5490")
            frame_attr.pack(pady=20)  # ← 8 a 20
            
            # ⭐ LABELS MÁS GRANDES (doble)
            tk.Label(
                frame_attr, text=f"{attr}:", font=("Arial", 24),  # ← 12 a 24
                fg="white", bg="#1a5490", width=14, anchor="w"  # ← width 12 a 14
            ).pack(side="left")
            
            # ⭐ SLIDERS MÁS GRANDES (doble)
            slider = tk.Scale(
                frame_attr, from_=0, to=3, orient="horizontal", length=500,  # ← 250 a 500
                bg="#2a6ab0", fg="white", font=("Arial", 20),  # ← 10 a 20
                width=30  # ← Agregar ancho del slider
            )
            slider.pack(side="left", padx=20)  # ← 10 a 20
            self.sliders[attr.lower()] = slider
            
            # ⭐ VALOR MÁS GRANDE (doble)
            label_val = tk.Label(
                frame_attr, text="0", font=("Arial", 24, "bold"),  # ← 12 a 24
                fg="yellow", bg="#1a5490", width=4  # ← width 3 a 4
            )
            label_val.pack(side="left")
            self.labels_valor[attr.lower()] = label_val
        
        # ⭐ LABEL PUNTOS RESTANTES MÁS GRANDE (doble)
        self.label_restantes = tk.Label(
            self.contenedor, text="Puntos restantes: 3",
            font=("Arial", 28, "bold"), fg="yellow", bg="#1a5490"  # ← 14 a 28
        )
        self.label_restantes.pack(pady=30)  # ← 15 a 30
        
        # Bind para actualizar
        for s in self.sliders.values():
            s.config(command=self.actualizar_total_puntos)
        
        # ⭐ BOTÓN MÁS GRANDE (doble)
        tk.Button(
            self.contenedor, text="✓ Confirmar",
            font=("Arial", 28, "bold"), command=self.confirmar_puntos,  # ← 14 a 28
            bg="#28a745", fg="white", width=20, height=3, cursor="hand2"  # ← width 15 a 20, height 2 a 3
        ).pack(pady=40)  # ← 20 a 40
    
    def actualizar_total_puntos(self, *args):
        """Actualiza el contador de puntos"""
        total = sum(s.get() for s in self.sliders.values())
        restantes = 3 - total
        self.label_restantes.config(text=f"Puntos restantes: {restantes}")
        
        # Actualizar labels
        for attr, slider in self.sliders.items():
            self.labels_valor[attr].config(text=str(slider.get()))
        
        # Deshabilitar sliders si ya usó 3 puntos
        for s in self.sliders.values():
            if restantes == 0 and s.get() == 0:
                s.config(state="disabled")
            else:
                s.config(state="normal")
    
    def confirmar_puntos(self):
        """Confirma la distribución de puntos"""
        puntos = {'fuerza': 0, 'inteligencia': 0, 'agilidad': 0, 'vitalidad': 0}
        for attr, slider in self.sliders.items():
            puntos[attr] = slider.get()
        
        total = sum(puntos.values())
        if total != 3:
            messagebox.showwarning("Error", "Debes distribuir exactamente 3 puntos")
            return
        
        self.personaje.distribuir_puntos(**puntos)
        self.mostrar_menu_principal()
    
    # ========================================================================
    # PANTALLA DE EVOLUCIÓN (NUEVA)
    # ========================================================================
    
    def mostrar_pantalla_evolucion(self):
        """Pantalla para elegir evolución (Luz u Oscuridad)"""
        self.limpiar_contenedor()
        
        # Título
        tk.Label(
            self.contenedor,
            text=f"🌟 ¡EVOLUCIÓN DISPONIBLE! 🌟",
            font=("Arial", 24, "bold"), fg="gold", bg="#1a5490"
        ).pack(pady=20)
        
        tk.Label(
            self.contenedor,
            text=f"Has alcanzado el nivel {self.personaje.nivel}",
            font=("Arial", 16), fg="white", bg="#1a5490"
        ).pack(pady=10)
        
        # Obtener opciones
        opciones = self.personaje.obtener_opciones_evolucion()
        
        if not opciones:
            messagebox.showerror("Error", "No hay evoluciones disponibles")
            self.mostrar_menu_principal()
            return
        
        # Frame para las dos opciones
        frame_opciones = tk.Frame(self.contenedor, bg="#1a5490")
        frame_opciones.pack(pady=30, padx=40, fill="both", expand=True)
        
        # OPCIÓN LUZ (IZQUIERDA)
        if "Luz" in opciones:
            frame_luz = tk.Frame(frame_opciones, bg="#ffd700", relief="raised", bd=5)
            frame_luz.pack(side="left", fill="both", expand=True, padx=10)
            
            luz_data = opciones["Luz"]
            
            tk.Label(
                frame_luz,
                text="☀️ CAMINO DE LUZ",
                font=("Arial", 18, "bold"),
                fg="#1a5490",
                bg="#ffd700"
            ).pack(pady=15)
            
            tk.Label(
                frame_luz,
                text=luz_data["nombre"],
                font=("Arial", 22, "bold"),
                fg="#ff8c00",
                bg="#ffd700"
            ).pack(pady=10)
            
            # Mostrar bonificaciones
            tk.Label(
                frame_luz,
                text="Bonificaciones:",
                font=("Arial", 14, "bold"),
                fg="#1a5490",
                bg="#ffd700"
            ).pack(pady=(20, 10))
            
            for attr, valor in luz_data["bonificaciones"].items():
                tk.Label(
                    frame_luz,
                    text=f"+{valor} {attr.capitalize()}",
                    font=("Arial", 16),
                    fg="#006400",
                    bg="#ffd700"
                ).pack(pady=5)
            
            # Botón elegir
            tk.Button(
                frame_luz,
                text="✨ ELEGIR LUZ",
                font=("Arial", 14, "bold"),
                bg="#ff8c00",
                fg="white",
                width=18,
                height=2,
                cursor="hand2",
                command=lambda: self.confirmar_evolucion("Luz")
            ).pack(pady=30)
        
        # OPCIÓN OSCURIDAD (DERECHA)
        if "Oscuridad" in opciones:
            frame_osc = tk.Frame(frame_opciones, bg="#4a0080", relief="raised", bd=5)
            frame_osc.pack(side="right", fill="both", expand=True, padx=10)
            
            osc_data = opciones["Oscuridad"]
            
            tk.Label(
                frame_osc,
                text="🌙 CAMINO DE OSCURIDAD",
                font=("Arial", 18, "bold"),
                fg="white",
                bg="#4a0080"
            ).pack(pady=15)
            
            tk.Label(
                frame_osc,
                text=osc_data["nombre"],
                font=("Arial", 22, "bold"),
                fg="#ff00ff",
                bg="#4a0080"
            ).pack(pady=10)
            
            # Mostrar bonificaciones
            tk.Label(
                frame_osc,
                text="Bonificaciones:",
                font=("Arial", 14, "bold"),
                fg="white",
                bg="#4a0080"
            ).pack(pady=(20, 10))
            
            for attr, valor in osc_data["bonificaciones"].items():
                tk.Label(
                    frame_osc,
                    text=f"+{valor} {attr.capitalize()}",
                    font=("Arial", 16),
                    fg="#ff00ff",
                    bg="#4a0080"
                ).pack(pady=5)
            
            # Botón elegir
            tk.Button(
                frame_osc,
                text="🔥 ELEGIR OSCURIDAD",
                font=("Arial", 14, "bold"),
                bg="#8b008b",
                fg="white",
                width=18,
                height=2,
                cursor="hand2",
                command=lambda: self.confirmar_evolucion("Oscuridad")
            ).pack(pady=30)
        
        # Texto informativo abajo
        tk.Label(
            self.contenedor,
            text="⚠️ Esta decisión es permanente y afectará tu progreso",
            font=("Arial", 12, "italic"),
            fg="yellow",
            bg="#1a5490"
        ).pack(side="bottom", pady=20)
    
    def confirmar_evolucion(self, camino):
        """Confirma y aplica la evolución elegida"""
        # ⭐ Deshabilitar todos los botones para evitar doble clic
        for widget in self.contenedor.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        for btn in child.winfo_children():
                            if isinstance(btn, tk.Button):
                                btn.config(state="disabled")
        
        resultado = self.personaje.aplicar_evolucion(camino)
        
        if resultado["exito"]:
            # Mostrar mensaje de éxito
            mensaje = f"🎉 ¡EVOLUCIÓN COMPLETADA!\n\n"
            mensaje += f"{resultado['mensaje']}\n\n"
            mensaje += "Bonificaciones aplicadas:\n"
            for attr, valor in resultado["bonificaciones"].items():
                mensaje += f"  +{valor} {attr.capitalize()}\n"
            
            messagebox.showinfo("✨ Evolución", mensaje)
            
            # ⭐ IMPORTANTE: Ir directamente a distribuir puntos NORMALES
            # sin volver a verificar si puede evolucionar
            self.mostrar_distribucion_puntos_sin_verificar()
        else:
            messagebox.showerror("Error", resultado["mensaje"])
            self.mostrar_menu_principal()
    
    def mostrar_distribucion_puntos_sin_verificar(self):
        """Pantalla para distribuir puntos SIN verificar evolución (ya evolucionó)"""
        self.limpiar_contenedor()
        
        # ⭐ TÍTULO MÁS GRANDE (doble)
        tk.Label(
            self.contenedor,
            text=f"🎉 ¡Subiste al nivel {self.personaje.nivel}!",
            font=("Arial", 40, "bold"), fg="white", bg="#1a5490"
        ).pack(pady=50)
        
        # ⭐ SUBTÍTULO MÁS GRANDE (doble)
        tk.Label(
            self.contenedor, text="Distribuye 3 puntos entre tus atributos:",
            font=("Arial", 28), fg="white", bg="#1a5490"
        ).pack(pady=20)
        
        # Frame para sliders
        frame_sliders = tk.Frame(self.contenedor, bg="#1a5490")
        frame_sliders.pack(pady=40)
        
        if self.personaje._usa_fuerza:
            atributos = ["Fuerza", "Agilidad", "Vitalidad"]
        else:
            atributos = ["Inteligencia", "Agilidad", "Vitalidad"]
        
        self.sliders = {}
        self.labels_valor = {}
        
        for attr in atributos:
            frame_attr = tk.Frame(frame_sliders, bg="#1a5490")
            frame_attr.pack(pady=20)
            
            # ⭐ LABELS MÁS GRANDES (doble)
            tk.Label(
                frame_attr, text=f"{attr}:", font=("Arial", 24),
                fg="white", bg="#1a5490", width=14, anchor="w"
            ).pack(side="left")
            
            # ⭐ SLIDERS MÁS GRANDES (doble)
            slider = tk.Scale(
                frame_attr, from_=0, to=3, orient="horizontal", length=500,
                bg="#2a6ab0", fg="white", font=("Arial", 20),
                width=30
            )
            slider.pack(side="left", padx=20)
            self.sliders[attr.lower()] = slider
            
            # ⭐ VALOR MÁS GRANDE (doble)
            label_val = tk.Label(
                frame_attr, text="0", font=("Arial", 24, "bold"),
                fg="yellow", bg="#1a5490", width=4
            )
            label_val.pack(side="left")
            self.labels_valor[attr.lower()] = label_val
        
        # ⭐ LABEL PUNTOS RESTANTES MÁS GRANDE (doble)
        self.label_restantes = tk.Label(
            self.contenedor, text="Puntos restantes: 3",
            font=("Arial", 28, "bold"), fg="yellow", bg="#1a5490"
        )
        self.label_restantes.pack(pady=30)
        
        # Bind para actualizar
        for s in self.sliders.values():
            s.config(command=self.actualizar_total_puntos)
        
        # ⭐ BOTÓN MÁS GRANDE (doble)
        tk.Button(
            self.contenedor, text="✓ Confirmar",
            font=("Arial", 28, "bold"), command=self.confirmar_puntos,
            bg="#28a745", fg="white", width=20, height=3, cursor="hand2"
        ).pack(pady=40)
    
    # ========================================================================
    # OTRAS ACCIONES
    # ========================================================================
    
    def sanar_personaje(self):
        """Sana al personaje"""
        resultado = SistemaSanacion.sanar_personaje(self.personaje)
        
        if resultado['exito']:
            self.historial.registrar_sanacion(resultado)
            messagebox.showinfo("✓ Sanación", resultado['mensaje'])
        else:
            messagebox.showwarning("✗ Error", resultado['mensaje'])
        
        self.mostrar_menu_principal()
    
    def ver_historial(self):
        """Muestra el historial detallado"""
        resumen = self.historial.obtener_resumen()
        registros = self.historial.obtener_historial()  # Ahora sí existe
        
        # Calcular winrate
        if resumen['combates_totales'] > 0:
            winrate = (resumen['victorias'] / resumen['combates_totales']) * 100
        else:
            winrate = 0
        
        # Construir mensaje con resumen
        mensaje = f"""📜 HISTORIAL DE {resumen['nombre'].upper()}

Clase: {resumen['clase_inicial']}
Nivel actual: {resumen['nivel_final']}

═══════════════════════════════════════
ESTADÍSTICAS GENERALES
═══════════════════════════════════════
Combates totales: {resumen['combates_totales']}
  ✓ Victorias: {resumen['victorias']}
  ✗ Derrotas: {resumen['derrotas']}
  Winrate: {winrate:.1f}%

Sanaciones realizadas: {resumen['sanaciones']}
💰 Dinero acumulado: ${resumen['dinero_final']}

═══════════════════════════════════════
REGISTRO DETALLADO DE ACCIONES
═══════════════════════════════════════
"""
        
        # Agregar cada acción del historial
        if registros:
            for i, registro in enumerate(registros[-10:], 1):  # Últimas 10 acciones
                if registro['tipo'] == 'combate':
                    icono = "⚔️" if registro['resultado'] == "Victoria" else "💀"
                    mensaje += f"\n{i}. {icono} Combate - {registro['resultado']}"
                    mensaje += f"\n   Fecha: {registro['fecha']}"
                elif registro['tipo'] == 'sanacion':
                    mensaje += f"\n{i}. 💊 Sanación (+{registro['hp_recuperado']} HP)"
                    mensaje += f"\n   Fecha: {registro['fecha']}"
        else:
            mensaje += "\nAún no hay acciones registradas."
        
        if len(registros) > 10:
            mensaje += f"\n\n... y {len(registros)-10} acciones más"
        
        # Crear ventana personalizada para el historial
        self.mostrar_ventana_historial(mensaje)
    
    def mostrar_ventana_historial(self, mensaje):
        """Muestra una ventana con el historial completo"""
        ventana = tk.Toplevel(self.ventana)
        ventana.title("📜 Historial Detallado")
        ventana.geometry("700x550")
        ventana.configure(bg="#1a5490")
        ventana.transient(self.ventana)
        
        # Header
        tk.Label(
            ventana,
            text="📜 HISTORIAL COMPLETO",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#1a5490"
        ).pack(pady=15)
        
        # Frame con scroll
        frame = tk.Frame(ventana, bg="white")
        frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        text = tk.Text(
            frame,
            font=("Consolas", 11),  # Fuente más grande y moderna
            yscrollcommand=scrollbar.set,
            wrap="word",
            bg="#f8f9fa",
            padx=15,
            pady=10
        )
        text.pack(fill="both", expand=True)
        scrollbar.config(command=text.yview)
        
        # Insertar mensaje
        text.insert("1.0", mensaje)
        text.config(state="disabled")
        
        # Botón cerrar
        tk.Button(
            ventana,
            text="✓ Cerrar",
            font=("Arial", 13, "bold"),
            command=ventana.destroy,
            bg="#007bff",
            fg="white",
            width=15,
            height=2,
            cursor="hand2"
        ).pack(pady=15)
    
    def ver_personajes_retirados(self):
        """Muestra lista de personajes retirados desde archivos JSON"""
        import glob
        
        # Buscar todos los archivos historial_*.json
        archivos_historial = glob.glob("historial_*.json")
        
        if not archivos_historial:
            messagebox.showinfo(
                "👥 Personajes Retirados",
                "No hay personajes retirados aún.\n\n"
                "📌 IMPORTANTE:\n"
                "• HUIR del combate NO retira al personaje\n"
                "• Para retirar, usa el botón 🚪 RETIRAR\n"
                "  desde el menú principal\n\n"
                "Solo los personajes retirados\n"
                "se guardan en el Salón de la Fama."
            )
            return
        
        # Leer todos los historiales
        personajes_info = []
        for archivo in archivos_historial:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    resumen = datos.get('resumen', {})
                    personajes_info.append({
                        'nombre': resumen.get('nombre', 'Desconocido'),
                        'clase': resumen.get('clase_inicial', '?'),
                        'nivel': resumen.get('nivel_final', 0),
                        'victorias': resumen.get('victorias', 0),
                        'combates': resumen.get('combates_totales', 0),
                        'dinero': resumen.get('dinero_final', 0),
                        'archivo': archivo
                    })
            except:
                continue
        
        if not personajes_info:
            messagebox.showinfo("Error", "No se pudieron leer los archivos de historial")
            return
        
        # Ordenar por nivel (descendente)
        personajes_info.sort(key=lambda x: x['nivel'], reverse=True)
        
        # Construir mensaje
        mensaje = "👥 SALÓN DE LA FAMA - PERSONAJES RETIRADOS\n"
        mensaje += "=" * 50 + "\n\n"
        
        for i, p in enumerate(personajes_info, 1):
            winrate = (p['victorias'] / max(1, p['combates'])) * 100
            mensaje += f"{i}. {p['nombre']} ({p['clase']} Nv.{p['nivel']})\n"
            mensaje += f"   💰 ${p['dinero']} | ⚔️ {p['victorias']}V/{p['combates']-p['victorias']}D ({winrate:.0f}%)\n\n"
        
        mensaje += "=" * 50 + "\n"
        mensaje += f"Total de héroes retirados: {len(personajes_info)}"
        
        # Mostrar en ventana con scroll
        self.mostrar_ventana_scroll("👥 Personajes Retirados", mensaje)
    
    def mostrar_ventana_scroll(self, titulo, mensaje):
        """Ventana genérica con scroll para texto largo"""
        ventana = tk.Toplevel(self.ventana)
        ventana.title(titulo)
        ventana.geometry("700x550")
        ventana.configure(bg="#1a5490")
        ventana.transient(self.ventana)
        
        tk.Label(
            ventana, text=titulo,
            font=("Arial", 18, "bold"), fg="white", bg="#1a5490"
        ).pack(pady=15)
        
        frame = tk.Frame(ventana, bg="white")
        frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        text = tk.Text(
            frame, font=("Consolas", 11),
            yscrollcommand=scrollbar.set, wrap="word", bg="#f8f9fa",
            padx=15, pady=10
        )
        text.pack(fill="both", expand=True)
        scrollbar.config(command=text.yview)
        
        text.insert("1.0", mensaje)
        text.config(state="disabled")
        
        tk.Button(
            ventana, text="✓ Cerrar", font=("Arial", 13, "bold"),
            command=ventana.destroy, bg="#007bff", fg="white",
            width=15, height=2, cursor="hand2"
        ).pack(pady=15)
    
    def retirar_personaje(self):
        """Retira al personaje"""
        respuesta = messagebox.askyesno(
            "⚠️ Retirar",
            f"¿Retirar a {self.personaje.nombre}?\n\nEsto es permanente."
        )
        
        if respuesta:
            self.personaje.marcar_retirado()
            exito, msg = self.historial.guardar_en_archivo()
            messagebox.showinfo("👋 Adiós", f"Gracias por jugar!\n\n{msg}")
            self.ventana.quit()
    
    def salir_juego(self):
        """Sale del juego"""
        if messagebox.askyesno("Salir", "¿Salir sin guardar?"):
            self.ventana.quit()
    
    def ejecutar(self):
        """Inicia el juego"""
        self.ventana.mainloop()

if __name__ == "__main__":
    juego = JuegoRPG()
    juego.ejecutar()
