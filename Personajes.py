# clases_personaje.py
from personaje_base import Personaje

class Guerrero(Personaje):
    def __init__(self, nombre):
        super().__init__(nombre, "Guerrero")
        self._usa_fuerza = True
        self.fuerza = 10
        self.agilidad = 5
        self.vitalidad = 5
        self.calcular_hp()
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
        self.inteligencia = 10
        self.agilidad = 5
        self.vitalidad = 5
        self.calcular_hp()
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
        self.inteligencia = 5
        self.agilidad = 5
        self.vitalidad = 10
        self.calcular_hp()
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
        self.fuerza = 5
        self.agilidad = 10
        self.vitalidad = 5
        self.calcular_hp()
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
