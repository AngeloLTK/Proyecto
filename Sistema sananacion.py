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
    