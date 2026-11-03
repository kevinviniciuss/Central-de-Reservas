"""carga.py - le a base de campo, carrega nas arvores e converte datas.

Instantes sao MINUTOS INTEIROS desde 11/10/2026 00:00 (dia 0 da serie, um domingo).
"""

import json
import unicodedata
from arvore import Arvore

ANO = 2026
DIAS_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]   # 2026 nao e bissexto
SEMANA = ["dom", "seg", "ter", "qua", "qui", "sex", "sab"]
ORIGEM_DIA, ORIGEM_MES = 11, 10


def _dia_do_ano(d, m):
    return sum(DIAS_MES[:m - 1]) + d


_ORIGEM_DOA = _dia_do_ano(ORIGEM_DIA, ORIGEM_MES)


def carregar_reservas(caminho="reservas_protec.json"):
    """Le o JSON da base e devolve (reservas em ORDEM CRONOLOGICA, base).
    Chave: instante de inicio; empate: id. E assim que uma agenda volta do disco."""
    with open(caminho, encoding="utf-8") as f:
        base = json.load(f)
    # ordenar aqui e a leitura da agenda gravada em ordem cronologica; a estrutura
    # do grupo (a arvore) nao usa sorted().
    return sorted(base["reservas"], key=lambda r: (r["inicio"], r["id"])), base


def gravar_reservas(caminho, base, reservas):
    base = dict(base)
    base["reservas"] = reservas
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=1)


def carregar_na_arvore(reservas, balanceada):
    arv = Arvore(balanceada=balanceada)
    for r in reservas:
        arv.inserir(r["inicio"], r)
    return arv


# ------------------------------------------------------------------- datas
def para_minutos(texto):
    """'dd/mm/aaaa hh:mm' (ou 'dd/mm hh:mm', ano 2026) -> minutos desde a origem.
    Levanta ValueError com mensagem clara se o texto for invalido."""
    try:
        data, hora = texto.strip().split()
        partes = data.split("/")
        d, m = int(partes[0]), int(partes[1])
        a = int(partes[2]) if len(partes) > 2 else ANO
        h, mi = hora.split(":")
        h, mi = int(h), int(mi)
    except (ValueError, IndexError):
        raise ValueError("use o formato dd/mm/aaaa hh:mm (ex.: 12/10/2026 19:00)")
    if a != ANO:
        raise ValueError("a base cobre apenas %d" % ANO)
    if not (1 <= m <= 12) or not (1 <= d <= DIAS_MES[m - 1]):
        raise ValueError("data inexistente")
    if not (0 <= h <= 23 and 0 <= mi <= 59):
        raise ValueError("hora inexistente")
    return (_dia_do_ano(d, m) - _ORIGEM_DOA) * 1440 + h * 60 + mi


def hora(minutos):
    h, m = divmod(minutos % 1440, 60)
    return "%02d:%02d" % (h, m)


def rotulo(minutos):
    """minutos -> 'dom 11/10 17:00' (so para exibir)."""
    dia = minutos // 1440
    doa = _ORIGEM_DOA + dia
    mes = 1
    while doa > DIAS_MES[mes - 1]:
        doa -= DIAS_MES[mes - 1]
        mes += 1
    return "%s %02d/%02d %s" % (SEMANA[dia % 7], doa, mes, hora(minutos))


# -------------------------------------------------------------- prioridade
# Politica PROPOSTA no E1 (secao 7), ainda a validar com o setor:
#   1 = institucional oficial / administracao     2 = academico, cerimonia, curso
#   3 = projeto, acao de departamento ou grupo    4 = demais solicitacoes
# A base de campo nao traz a classe; ela e deduzida da descricao pelas palavras
# abaixo (a primeira regra que casar vale). Se a reserva tiver o campo
# "prioridade", ele manda.
PRIORIDADES = {1: "institucional", 2: "acadêmico", 3: "projeto", 4: "demais"}
_REGRAS = (
    (1, ("culto", "capela", "escola sabatina", "santa ceia", "celebracao")),
    (2, ("aula", "mestrado", "semana", "forum", "convencao", "congresso",
         "reuniao divisao", "dia do educador", "recital", "concerto")),
    (3, ("ensaio", "sarau", "noite literaria", "unasp experience", "rumo ao",
         "celebrando", "reuniao")),
)


def _sem_acento(texto):
    base = unicodedata.normalize("NFD", texto)
    return "".join(ch for ch in base if unicodedata.category(ch) != "Mn").lower()


def prioridade(reserva):
    """Classe de prioridade (1 a 4; menor = mais urgente) de uma reserva."""
    p = reserva.get("prioridade")
    if isinstance(p, int) and 1 <= p <= 4:
        return p
    desc = _sem_acento(reserva["descricao"])
    for classe, palavras in _REGRAS:
        for pal in palavras:
            if pal in desc:
                return classe
    return 4
