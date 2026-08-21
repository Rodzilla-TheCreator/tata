# Campo de protección de un escáner de seguridad · ISO 13855 aplicado a AGV
# S = v·(t_escáner + t_controlador + t_freno) + distancia de frenado + tolerancias
T_ESC, T_PLC, T_FRENO = 0.080, 0.050, 0.200      # s · escáner ≤80 ms, PLC+contactor, respuesta del freno
DECEL = 2.0                                       # m/s² · frenado de servicio cargado
Z_TOL = 0.10                                      # m · tolerancia de medición del escáner
t_reac = T_ESC + T_PLC + T_FRENO
print(f"Tiempo de reacción total: {t_reac*1000:.0f} ms  (escáner {T_ESC*1000:.0f} + control {T_PLC*1000:.0f} + freno {T_FRENO*1000:.0f})\n")
print(f"{'velocidad':>10} {'recorre reaccionando':>21} {'frena en':>10} {'CAMPO MÍNIMO':>14}")
for v in (0.5, 1.0, 1.5, 2.0, 3.3):
    d_reac, d_freno = v*t_reac, v*v/(2*DECEL)
    S = d_reac + d_freno + Z_TOL
    print(f"{v:>8.1f} m/s {d_reac:>18.2f} m {d_freno:>9.2f} m {S:>12.2f} m")
print("\nEl pasillo de la propuesta mide 5.54 m; el actual, 3.17 m.")
print("Un montacargas de 1.15 m de ancho deja 2.20 m libres por lado en el propuesto,")
print("y 1.01 m en el actual — por eso el campo se conmuta al entrar al pasillo.")
