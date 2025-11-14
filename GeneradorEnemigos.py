
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
