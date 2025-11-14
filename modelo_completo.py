"""
MODELO COMPLETO - Sistema RPG
Proyecto Ingeniería de Software - Grupo 6
"""


import random
import json
from enum import Enum
from datetime import datetime

class EstadoPersonaje(Enum):
    ACTIVO = "Activo"
    RETIRADO = "Retirado"
    MUERTO = "Muerto"

class Personaje:
    def __init__(self, nombre, clase):
        self.nombre = nombre
        self.clase = clase
        self.nivel = 1
        self.dinero = 100
        self.fuerza = 0
        self.inteligencia = 0
        self.agilidad = 0
        self.vitalidad = 0
        self.estado = EstadoPersonaje.ACTIVO
        self.hp = 0
        self.camino_evolucion = []
        self.evolucion_actual = clase
        self.imagen_path = None
        self._usa_fuerza = True
    
    def calcular_hp(self):
        self.hp = self.vitalidad // 2
        return self.hp
    
    def atacar(self, enemigo):
        probabilidad_golpe = 100 - enemigo.agilidad
        dado = random.randint(1, 100)
        if dado <= probabilidad_golpe:
            daño = self._calcular_daño()
            enemigo.recibir_daño(daño)
            return (True, daño)
        return (False, 0)
    
    def _calcular_daño(self):
        atributo = self.fuerza if self._usa_fuerza else self.inteligencia
        return max(1, atributo // 20)
    
    def recibir_daño(self, daño):
        self.hp = max(0, self.hp - daño)
        if self.hp == 0:
            self.estado = EstadoPersonaje.MUERTO
    
    def sanar(self, hp_recuperado):
        hp_maximo = self.vitalidad // 2
        self.hp = min(hp_maximo, self.hp + hp_recuperado)
    
    def subir_nivel(self):
        self.nivel += 1
    
    def distribuir_puntos(self, fuerza=0, inteligencia=0, agilidad=0, vitalidad=0):
        if fuerza + inteligencia + agilidad + vitalidad != 3:
            raise ValueError("Debes distribuir exactamente 3 puntos")
        hp_porcentaje = self.hp / max(1, self.vitalidad // 2)
        self.fuerza += fuerza
        self.inteligencia += inteligencia
        self.agilidad += agilidad
        self.vitalidad += vitalidad
        self.calcular_hp()
        self.hp = int(self.hp * hp_porcentaje)
    
    def esta_vivo(self):
        return self.hp > 0 and self.estado == EstadoPersonaje.ACTIVO
    
    def marcar_retirado(self):
        """Marca al personaje como retirado"""
        self.estado = EstadoPersonaje.RETIRADO
    
    def puede_evolucionar(self):
        """Verifica si el personaje puede evolucionar"""
        return self.nivel in [10, 20] and len(self.camino_evolucion) < 2
    
    def obtener_opciones_evolucion(self):
        """Retorna las opciones de evolución disponibles"""
        if not self.puede_evolucionar():
            return None
        
        if not hasattr(self, 'evolucionesDisp'):
            return None
        
        nivel_key = f"nivel_{self.nivel}"
        if nivel_key not in self.evolucionesDisp:
            return None
        
        return self.evolucionesDisp[nivel_key]
    
    def aplicar_evolucion(self, camino):
        """
        Aplica la evolución según el camino elegido (Luz u Oscuridad)
        
        Args:
            camino (str): "Luz" u "Oscuridad"
        
        Returns:
            dict: Información sobre la evolución aplicada
        """
        if not self.puede_evolucionar():
            return {"exito": False, "mensaje": "No puedes evolucionar en este nivel"}
        
        opciones = self.obtener_opciones_evolucion()
        if not opciones or camino not in opciones:
            return {"exito": False, "mensaje": "Opción de evolución inválida"}
        
        evolucion = opciones[camino]
        
        # Guardar la elección
        self.camino_evolucion.append(camino)
        
        # Actualizar nombre de evolución
        nombre_anterior = self.evolucion_actual
        self.evolucion_actual = evolucion["nombre"]
        
        # Aplicar bonificaciones
        bonificaciones = evolucion["bonificaciones"]
        hp_porcentaje = self.hp / max(1, self.vitalidad // 2)
        
        for atributo, bonus in bonificaciones.items():
            if atributo == "fuerza":
                self.fuerza += bonus
            elif atributo == "inteligencia":
                self.inteligencia += bonus
            elif atributo == "agilidad":
                self.agilidad += bonus
            elif atributo == "vitalidad":
                self.vitalidad += bonus
        
        # Recalcular HP manteniendo el porcentaje
        self.calcular_hp()
        self.hp = int(self.hp * hp_porcentaje)
        
        return {
            "exito": True,
            "mensaje": f"¡Evolucionaste de {nombre_anterior} a {self.evolucion_actual}!",
            "nombre_anterior": nombre_anterior,
            "nombre_nuevo": self.evolucion_actual,
            "bonificaciones": bonificaciones
        }
    
    def obtener_info(self):
        return {
            "nombre": self.nombre, "clase": self.clase,
            "evolucion": self.evolucion_actual, "nivel": self.nivel,
            "hp": self.hp, "hp_maximo": self.vitalidad // 2,
            "fuerza": self.fuerza, "inteligencia": self.inteligencia,
            "agilidad": self.agilidad, "vitalidad": self.vitalidad,
            "dinero": self.dinero, "estado": self.estado.value
        }
    
    def __str__(self):
        return f"{self.nombre} ({self.evolucion_actual} | nivel {self.nivel} | {self.hp} HP)"

class Guerrero(Personaje):
    def __init__(self, nombre):
        super().__init__(nombre, "Guerrero")
        self._usa_fuerza = True
        # Atributos base 
        self.fuerza = 10
        self.agilidad = 5
        self.vitalidad = 5
        self.calcular_hp()
        
        # Diccionario de evoluciones
        self.evolucionesDisp = {
            "nivel_10": {
                "Luz": {"nombre": "Caballero", "bonificaciones": {"vitalidad": 10}},
                "Oscuridad": {"nombre": "Gladiador", "bonificaciones": {"fuerza": 10}}
            },
            "nivel_20": {
                "Luz": {"nombre": "Paladín", "bonificaciones": {"fuerza": 10, "vitalidad": 5}},
                "Oscuridad": {"nombre": "Señor", "bonificaciones": {"fuerza": 5, "vitalidad": 10}}
            }
        }

class Mago(Personaje):
    def __init__(self, nombre):
        super().__init__(nombre, "Mago")
        self._usa_fuerza = False
        # Atributos base 
       
        self.inteligencia = 10
        self.agilidad = 5
        self.vitalidad = 5
        self.calcular_hp()
        
        # Diccionario de evoluciones
        self.evolucionesDisp = {
            "nivel_10": {
                "Luz": {"nombre": "Hechicero", "bonificaciones": {"inteligencia": 10}},
                "Oscuridad": {"nombre": "Brujo", "bonificaciones": {"vitalidad": 10}}
            },
            "nivel_20": {
                "Luz": {"nombre": "Gran Divinador", "bonificaciones": {"inteligencia": 10, "agilidad": 5}},
                "Oscuridad": {"nombre": "Archimago", "bonificaciones": {"agilidad": 10, "vitalidad": 5}}
            }
        }

class Clerigo(Personaje):
    def __init__(self, nombre):
        super().__init__(nombre, "Clérigo")
        self._usa_fuerza = False
        # Atributos base 
       
        self.inteligencia = 5
        self.agilidad = 5
        self.vitalidad = 10
        self.calcular_hp()
        
        # Diccionario de evoluciones
        self.evolucionesDisp = {
            "nivel_10": {
                "Luz": {"nombre": "Sacerdote", "bonificaciones": {"vitalidad": 10}},
                "Oscuridad": {"nombre": "Chamán", "bonificaciones": {"inteligencia": 10}}
            },
            "nivel_20": {
                "Luz": {"nombre": "Obispo", "bonificaciones": {"inteligencia": 5, "vitalidad": 10}},
                "Oscuridad": {"nombre": "Sabio", "bonificaciones": {"inteligencia": 10, "vitalidad": 5}}
            }
        }

class Luchador(Personaje):
    def __init__(self, nombre):
        super().__init__(nombre, "Luchador")
        self._usa_fuerza = True
        # Atributos base
        self.fuerza = 5
        self.agilidad = 10
        self.vitalidad = 5
        self.calcular_hp()
        
        # Diccionario de evoluciones
        self.evolucionesDisp = {
            "nivel_10": {
                "Luz": {"nombre": "Monje", "bonificaciones": {"agilidad": 10}},
                "Oscuridad": {"nombre": "Berserker", "bonificaciones": {"vitalidad": 10}}
            },
            "nivel_20": {
                "Luz": {"nombre": "Puño Divino", "bonificaciones": {"agilidad": 10, "vitalidad": 5}},
                "Oscuridad": {"nombre": "Monje Vengador", "bonificaciones": {"fuerza": 10, "agilidad": 5}}
            }
        }

class Combate:
    def __init__(self, personaje1, personaje2):
        self.personaje1 = personaje1
        self.personaje2 = personaje2
        self.turno_actual = 1
        self.log_combate = []
        self.ganador = None
        self.combate_iniciado = False
        
        # Determinar orden
        if personaje1.agilidad >= personaje2.agilidad:
            self.atacante = personaje1
            self.defensor = personaje2
        else:
            self.atacante = personaje2
            self.defensor = personaje1
    
    def obtener_mensaje_inicial(self):
        """Retorna el mensaje inicial del combate"""
        return f"¡Empieza el combate!\n{self.personaje1} contra {self.personaje2}"
    
    def ejecutar_turno_completo(self):
        """
        Ejecuta UN turno completo (ambos personajes atacan)
        Retorna: (continua, mensajes_turno)
        """
        mensajes = []
        mensajes.append(f"\n--- Turno {self.turno_actual} ---")
        
        # Ataque del primero
        if self.atacante.esta_vivo():
            exito, daño = self.atacante.atacar(self.defensor)
            if exito:
                msg = f"  • {self.atacante.nombre} ataca a {self.defensor.nombre}, causando {daño} de daño. {self.defensor.nombre} tiene {self.defensor.hp} HP restantes."
            else:
                msg = f"  • {self.atacante.nombre} ataca a {self.defensor.nombre}, pero falla. {self.defensor.nombre} no sufre daño."
            mensajes.append(msg)
            
            if not self.defensor.esta_vivo():
                mensajes.append(f"  • {self.defensor.nombre} tiene 0 HP y no puede seguir peleando.")
        
        # Ataque del segundo (si sigue vivo)
        if self.defensor.esta_vivo():
            exito, daño = self.defensor.atacar(self.atacante)
            if exito:
                msg = f"  • {self.defensor.nombre} ataca a {self.atacante.nombre}, causando {daño} de daño. {self.atacante.nombre} tiene {self.atacante.hp} HP restantes."
            else:
                msg = f"  • {self.defensor.nombre} ataca a {self.atacante.nombre}, pero falla. {self.atacante.nombre} no sufre daño."
            mensajes.append(msg)
            
            if not self.atacante.esta_vivo():
                mensajes.append(f"  • {self.atacante.nombre} tiene 0 HP y no puede seguir peleando.")
        
        self.turno_actual += 1
        self.log_combate.extend(mensajes)
        
        # Verificar si el combate terminó
        continua = self.personaje1.esta_vivo() and self.personaje2.esta_vivo()
        
        return (continua, mensajes)
    
    def finalizar_combate(self):
        """Finaliza el combate y retorna resultado"""
        self.ganador = self.personaje1 if self.personaje1.esta_vivo() else self.personaje2
        es_victoria = self.ganador == self.personaje1
        
        if es_victoria:
            self.personaje1.dinero += 50
            self.personaje1.subir_nivel()
            self.log_combate.append(f"\n¡{self.personaje1.nombre} gana el combate y recibe 50 pesos!")
            self.log_combate.append(f"{self.personaje1.nombre} sube al nivel {self.personaje1.nivel}!")
        else:
            self.personaje1.dinero = max(0, self.personaje1.dinero - 50)
            self.log_combate.append(f"\n{self.personaje2.nombre} gana el combate. {self.personaje1.nombre} pierde 50 pesos.")
        
        return {
            "ganador": self.ganador,
            "es_victoria": es_victoria,
            "log": self.log_combate,
            "subio_nivel": es_victoria,
            "dinero_cambio": 50 if es_victoria else -50
        }

class GeneradorEnemigos:
    @staticmethod
    def generar_enemigo(nivel_jugador):
        nivel = random.randint(max(1, nivel_jugador - 2), nivel_jugador + 1)
        ClaseEnemigo = random.choice([Guerrero, Mago, Clerigo, Luchador])
        enemigo = ClaseEnemigo(ClaseEnemigo.__name__)
        for _ in range(nivel - 1):
            enemigo.subir_nivel()
            puntos = [1, 1, 1]
            random.shuffle(puntos)
            if enemigo._usa_fuerza:
                enemigo.distribuir_puntos(fuerza=puntos[0], agilidad=puntos[1], vitalidad=puntos[2])
            else:
                enemigo.distribuir_puntos(inteligencia=puntos[0], agilidad=puntos[1], vitalidad=puntos[2])
        enemigo.calcular_hp()
        return enemigo

class SistemaSanacion:
    COSTO_SANACION = 20
    
    @staticmethod
    def puede_sanar(personaje):
        # Permitir sanación incluso con 0 HP (cuando más se necesita)
        if personaje.dinero < SistemaSanacion.COSTO_SANACION:
            return (False, f"No tienes suficiente dinero. Necesitas ${SistemaSanacion.COSTO_SANACION}.")
        if personaje.hp >= personaje.vitalidad // 2:
            return (False, "Tu HP ya está al máximo.")
        return (True, "Puedes sanar.")
    
    @staticmethod
    def sanar_personaje(personaje):
        puede, mensaje = SistemaSanacion.puede_sanar(personaje)
        if not puede:
            return {"exito": False, "mensaje": mensaje}
        base = personaje.vitalidad // 4
        hp_antes = personaje.hp
        personaje.sanar(base + random.randint(0, base))
        personaje.dinero -= SistemaSanacion.COSTO_SANACION
        return {
            "exito": True, "mensaje": f"Recuperaste {personaje.hp - hp_antes} HP.",
            "hp_recuperado": personaje.hp - hp_antes,
            "hp_actual": personaje.hp, "hp_maximo": personaje.vitalidad // 2,
            "dinero_restante": personaje.dinero, "costo": SistemaSanacion.COSTO_SANACION
        }

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