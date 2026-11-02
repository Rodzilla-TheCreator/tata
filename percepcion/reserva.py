# ─────────────────────────────────────────────────────────────────────────────
# Protocolo de reserva — exclusión mutua sobre los recursos que A y B comparten
#
# Recursos: las POSICIONES DE TRASBORDO del fondo y los HUECOS de rack (y la entrada y la
# salida de cada sector). Una reserva dice «este lugar es mío para esta tarea».
#
# LA REGLA ANTI-DEADLOCK QUE SE ELIGIÓ — todo o nada, en orden total, ANTES de tocar el cubo:
#   reservar_todo(equipo, [destino, origen]) toma los dos o ninguno, en una sola operación
#   atómica, y el equipo la pide ANTES de salir a recoger. Nunca se espera con algo en la mano.
#
#   Por qué rompe el ciclo: un deadlock necesita cuatro condiciones a la vez (Coffman):
#   exclusión mutua, retener-y-esperar, no expropiación y espera circular. Esta regla mata dos:
#     · RETENER-Y-ESPERAR: el equipo que no consigue todo no retiene nada (ni reserva ni cubo:
#       todavía no salió a recogerlo). Espera con las uñas vacías.
#     · ESPERA CIRCULAR: el orden total (huecos antes que trasbordo, después por id) queda como
#       defensa si algún día la reserva deja de ser una sola llamada atómica — por ejemplo,
#       repartida entre dos equipos por radio. Pedir siempre en el mismo orden no permite ciclos.
#
#   Lo que NO se eligió y por qué: expropiación por timeout. Quitarle la reserva a un equipo
#   que ya tiene el cubo en las uñas lo deja sin dónde soltarlo — el mismo bloqueo, más tarde.
#
# Los dos gestores de CONTROL (para que las pruebas puedan fallar):
#   GestorTonto       siempre dice sí y no lleva cuenta → dos equipos creen tener el mismo lugar
#   la política «tardía» del Equipo (fsm_estados.py) usa el gestor bueno pero reserva el
#   destino recién al llegar con el cubo → retiene-y-espera → deadlock de la línea 40
# ─────────────────────────────────────────────────────────────────────────────


def orden_total(recurso_id, tipos):
    """Huecos (y entrada/salida) antes que trasbordo; después por id. Ver arriba por qué."""
    return (1 if tipos.get(recurso_id) == "trasbordo" else 0, recurso_id)


class GestorDeReservas:
    def __init__(self, tipos):
        """tipos: id de recurso → 'hueco' | 'trasbordo' | 'entrada' | 'salida'."""
        self.tipos = dict(tipos)
        self.duenio = {r: None for r in self.tipos}
        self.pedidos = 0
        self.negados = 0

    def reservar(self, equipo, recurso):
        """Atómico: si dos piden el mismo recurso, gana exactamente uno."""
        self.pedidos += 1
        actual = self.duenio[recurso]
        if actual is None or actual == equipo:
            self.duenio[recurso] = equipo
            return True
        self.negados += 1
        return False

    def reservar_todo(self, equipo, recursos):
        """Todo o nada, en orden total. Si falla uno, suelta los que tomó en esta llamada."""
        tomados = []
        for r in sorted(set(recursos), key=lambda x: orden_total(x, self.tipos)):
            ya_era_mio = self.duenio[r] == equipo
            if not self.reservar(equipo, r):
                for t in tomados:
                    self.liberar(equipo, t)
                return False
            if not ya_era_mio:
                tomados.append(r)
        return True

    def liberar(self, equipo, recurso):
        if self.duenio.get(recurso) == equipo:
            self.duenio[recurso] = None

    def liberar_todo(self, equipo):
        for r, d in self.duenio.items():
            if d == equipo:
                self.duenio[r] = None

    def es_de(self, recurso):
        return self.duenio.get(recurso)

    def libre_para(self, equipo, recurso):
        return self.duenio.get(recurso) in (None, equipo)


class GestorTonto(GestorDeReservas):
    """CONTROL: siempre dice que sí y no recuerda nada. Si con este NO aparece la colisión,
    la prueba de la carrera no probó nada."""

    def reservar(self, equipo, recurso):
        self.pedidos += 1
        return True

    def reservar_todo(self, equipo, recursos):
        self.pedidos += 1
        return True

    def es_de(self, recurso):
        return None

    def libre_para(self, equipo, recurso):
        return True
