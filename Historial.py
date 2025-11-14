class Historial:
    def __init__(self, personaje):
        self.personaje = personaje
        self.registros = []
    
    def registrar_combate(self, resultado):
        self.registros.append({
            "tipo": "combate",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resultado": "Victoria" if resultado.get("es_victoria") else "Derrota"
        })
    
    def registrar_sanacion(self, resultado):
        self.registros.append({
            "tipo": "sanacion",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hp_recuperado": resultado.get("hp_recuperado", 0)
        })
    
    def obtener_historial(self):
        """Retorna la lista completa de registros"""
        return self.registros
    
    def obtener_resumen(self):
        combates = sum(1 for r in self.registros if r["tipo"] == "combate")
        victorias = sum(1 for r in self.registros if r["tipo"] == "combate" and r["resultado"] == "Victoria")
        return {
            "nombre": self.personaje.nombre, "clase_inicial": self.personaje.clase,
            "nivel_final": self.personaje.nivel, "combates_totales": combates,
            "victorias": victorias, "derrotas": combates - victorias,
            "sanaciones": sum(1 for r in self.registros if r["tipo"] == "sanacion"),
            "dinero_final": self.personaje.dinero
        }
    
    def guardar_en_archivo(self, nombre=None):
        nombre = nombre or f"historial_{self.personaje.nombre}.json"
        try:
            with open(nombre, 'w', encoding='utf-8') as f:
                json.dump({"resumen": self.obtener_resumen(), "registros": self.registros}, f, indent=4)
            return (True, f"Guardado en {nombre}")
        except Exception as e:
            return (False, str(e))