# personaje_base.py
import random
from estado import EstadoPersonaje

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
        self.estado = EstadoPersonaje.RETIRADO

    def puede_evolucionar(self):
        return self.nivel in [10, 20] and len(self.camino_evolucion) < 2

    def obtener_opciones_evolucion(self):
        if not self.puede_evolucionar():
            return None
        if not hasattr(self, 'evolucionesDisp'):
            return None
        nivel_key = f"nivel_{self.nivel}"
        return self.evolucionesDisp.get(nivel_key)

    def aplicar_evolucion(self, camino):
        if not self.puede_evolucionar():
            return {"exito": False, "mensaje": "No puedes evolucionar en este nivel"}

        opciones = self.obtener_opciones_evolucion()
        if not opciones or camino not in opciones:
            return {"exito": False, "mensaje": "Opción de evolución inválida"}

        evolucion = opciones[camino]
        self.camino_evolucion.append(camino)
        nombre_anterior = self.evolucion_actual
        self.evolucion_actual = evolucion["nombre"]

        bonificaciones = evolucion["bonificaciones"]
        hp_porcentaje = self.hp / max(1, self.vitalidad // 2)
        for atributo, bonus in bonificaciones.items():
            setattr(self, atributo, getattr(self, atributo) + bonus)

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
            "nombre": self.nombre,
            "clase": self.clase,
            "evolucion": self.evolucion_actual,
            "nivel": self.nivel,
            "hp": self.hp,
            "hp_maximo": self.vitalidad // 2,
            "fuerza": self.fuerza,
            "inteligencia": self.inteligencia,
            "agilidad": self.agilidad,
            "vitalidad": self.vitalidad,
            "dinero": self.dinero,
            "estado": self.estado.value
        }

    def __str__(self):
        return f"{self.nombre} ({self.evolucion_actual} | nivel {self.nivel} | {self.hp} HP)"
