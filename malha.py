from carga import janela_intervalo

PASSO = 30                      
H_INI, H_FIM = 6 * 60, 24 * 60  


def malha_dia(reservas, recurso, dia, passo=PASSO, ini=H_INI, fim=H_FIM):
    """Divide o dia de um recurso em trechos e classifica cada um:
    'uso'   -> alguma reserva em andamento (inicio..fim)
    'prep'  -> so a equipe presente (chegada_equipe..inicio)
    'livre' -> nada ocupa o trecho
    Reservas em espera nao contam."""
    base = dia * 1440
    doRecurso = [r for r in reservas
                 if r["recurso"] == recurso and r.get("status") != "em_espera"]
    trechos = []
    for t in range(ini, fim, passo):
        a, b = base + t, base + t + passo
        uso, prep = [], []
        for r in doRecurso:
            ji, jf = janela_intervalo(r)
            if jf <= a or ji >= b:
                continue
            fim_r = jf
            if r["inicio"] < b and fim_r > a:
                uso.append(r["id"])
            else:
                prep.append(r["id"])
        estado = "uso" if uso else ("prep" if prep else "livre")
        trechos.append({"de": a, "ate": b, "estado": estado, "ids": uso + prep})
    return trechos


def resumo(trechos):
    n = len(trechos)
    cont = {"uso": 0, "prep": 0, "livre": 0}
    for t in trechos:
        cont[t["estado"]] += 1
    cont["ocupacao"] = 100.0 * (cont["uso"] + cont["prep"]) / n if n else 0.0
    return cont