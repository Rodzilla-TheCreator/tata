# ─────────────────────────────────────────────────────────────────────────────
# Tres formas de mover un maxicubo · costo a 5 años
# Salario mínimo Honduras 2026, industria manufacturera 150+ trabajadores:
#   L 12,349.49/mes  ·  tipo de cambio promedio 2026: 26.61 HNL/USD
# ─────────────────────────────────────────────────────────────────────────────
TC = 26.61
MINIMO_HNL = 12349.49
BASE_HNL = 18000            # operador certificado ≈ 1.46× el mínimo
CARGAS = 1.27               # aguinaldo + catorceavo + IHSS + RAP + vacaciones + INFOP

base_usd = BASE_HNL / TC
op_mes = base_usd * CARGAS
op_anio = op_mes * 12
print(f"Salario mínimo manufactura 150+: L {MINIMO_HNL:,.0f}/mes = ${MINIMO_HNL/TC:,.0f}")
print(f"Operador certificado: L {BASE_HNL:,.0f}/mes = ${base_usd:,.0f}")
print(f"Costo cargado ({int((CARGAS-1)*100)}% de cargas): ${op_mes:,.0f}/mes = ${op_anio:,.0f}/año\n")

UNID, TURNOS = 3, 2
SOFT_ANIO = 4000            # software y monitoreo por unidad/año
FLETE = 0.20

esc = {}
# A · operadores, con los montacargas que ya tienen
esc['operadores'] = dict(
    capex=0, anual=op_anio * UNID * TURNOS,
    nota=f'{UNID} máquinas × {TURNOS} turnos = {UNID*TURNOS} operadores')
# B · montacargas autónomos de fábrica
FAB = 100000
esc['fabrica'] = dict(
    capex=UNID * FAB + UNID * 7500 + 30000,      # unidad + instalación/mapeo + integración
    anual=UNID * 4250,                            # mantenimiento y software de fábrica
    nota=f'{UNID} unidades nuevas a ${FAB:,} + instalación + integración')
# C · kit TaTa nivel 3 sobre las máquinas que ya tienen
KIT, INFRA = 22978, 14288
esc['tata'] = dict(
    capex=UNID * KIT * (1 + FLETE) + INFRA,
    anual=UNID * SOFT_ANIO,
    nota=f'{UNID} kits sobre sus propias máquinas + infraestructura del sitio')

print(f"{'':14} {'CapEx':>12} {'Anual':>11} {'Año 1':>11} {'Año 3':>11} {'Año 5':>11}")
for k, e in esc.items():
    a = [e['capex'] + e['anual'] * n for n in (1, 3, 5)]
    print(f"{k:14} {e['capex']:>12,.0f} {e['anual']:>11,.0f} {a[0]:>11,.0f} {a[1]:>11,.0f} {a[2]:>11,.0f}")

print("\n— Retorno del kit contra seguir con operadores —")
ahorro = esc['operadores']['anual'] - esc['tata']['anual']
print(f"Ahorro anual bruto: ${ahorro:,.0f}")
print(f"Inversión TaTa: ${esc['tata']['capex']:,.0f}")
print(f"Retorno: {esc['tata']['capex']/ahorro:.2f} años")
print(f"\nContra comprar autónomos de fábrica:")
print(f"Ahorro de CapEx: ${esc['fabrica']['capex'] - esc['tata']['capex']:,.0f}"
      f"  ({esc['fabrica']['capex']/esc['tata']['capex']:.1f}× más barato)")
import json; json.dump({k:{kk:round(vv,0) if isinstance(vv,(int,float)) else vv for kk,vv in v.items()} for k,v in esc.items()} | {'op_anio':round(op_anio)}, open('comparativa.json','w'))
