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