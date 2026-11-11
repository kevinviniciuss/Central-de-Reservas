import os
import re
import sys

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_TTY = sys.stdout.isatty() or os.environ.get("FORCAR_COR") == "1"
ATIVO = _TTY and os.environ.get("NO_COLOR") is None
if os.name == "nt":
    os.system("")   

CODIGOS = {
    "bold": "1", "dim": "2",
    "azul": "38;5;75", "ouro": "38;5;214", "branco": "38;5;255", "muted": "38;5;245",
    "ok": "38;5;78", "aviso": "38;5;220", "erro": "38;5;203",
    "bst": "38;5;209", "avl": "38;5;80",
    "banner": "1;38;5;255;48;5;24",
    "cab": "1;38;5;16;48;5;75",
    "rec_EST-01": "1;38;5;141",   # Auditorio do Estudio  
    "rec_AUD-01": "1;38;5;226",   # Auditorio Central     
    "rec_MAS-01": "1;38;5;33",    # Auditorio Masculino   
    "rec_FEM-01": "1;38;5;213",   # Auditorio Feminino    
    "rec_FAC-01": "1;38;5;41",    # Auditorio Faculdade   
    "rec_REI-01": "1;38;5;51",    # Auditorio Reitoria    
    "rec_IGR-01": "1;38;5;208",   # Igreja UNASP          
    "rec_EXT-01": "1;38;5;247",   # Externa               
    "faixa_ok": "1;38;5;16;48;5;78",
    "faixa_aviso": "1;38;5;16;48;5;220",
    "faixa_erro": "1;38;5;16;48;5;203",
}


def c(texto, *estilos):
    if not ATIVO:
        return str(texto)
    cod = ";".join(CODIGOS[e] for e in estilos)
    return "\x1b[%sm%s\x1b[0m" % (cod, texto)


def cor_recurso(codigo, texto=None):
    chave = "rec_" + codigo
    return c(texto if texto is not None else codigo, chave if chave in CODIGOS else "branco")


def tam(texto):
    return len(_ANSI.sub("", texto))


def ajustar(texto, largura, alinh="l"):
    falta = largura - tam(texto)
    if falta <= 0:
        return texto
    return (" " * falta + texto) if alinh == "r" else (texto + " " * falta)


def cortar(texto, largura):
    return texto if len(texto) <= largura else texto[:max(0, largura - 1)] + "…"


def largura():
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80
    return max(60, min(cols, 90))


def limpar():
    if _TTY:
        sys.stdout.write("\x1b[H\x1b[2J")
        sys.stdout.flush()
    else:
        print("\n" + "-" * 40)


def cabecalho(titulo, setor, passo=None, total=None):
    limpar()
    w = largura()
    esq = "  ◆ CENTRAL DE RESERVAS"
    dir_ = "setor %s  " % setor
    print(c(ajustar(esq, w - len(dir_)) + dir_, "banner"))
    print()
    sufixo = ("passo %d de %d" % (passo, total)) if passo else ""
    print("  " + c(titulo, "bold", "ouro") + ("   " + c(sufixo, "muted") if sufixo else ""))
    print(c("  " + "─" * (w - 4), "muted"))
    print()


def resumo(pares):
    for rotulo, valor in pares:
        if "\x1b" not in str(valor):   
            valor = c(valor, "branco")
        print("  " + c(ajustar(rotulo, 10), "muted") + valor)
    print()


def secao(titulo):
    print()
    print("  " + c("▌ " + titulo, "bold", "azul"))
    print()


def ok(msg):
    print("  " + c("✔", "ok") + " " + msg)


def erro(msg):
    print("  " + c("✖", "erro") + " " + c(msg, "erro"))


def aviso(msg):
    print("  " + c("▲", "aviso") + " " + c(msg, "aviso"))


def info(msg):
    print("  " + c("●", "azul") + " " + msg)


def faixa(texto, tipo="ok"):
    print("  " + c(" %s " % texto, "faixa_" + tipo))


def ler(rotulo, dica=None):
    linha = "  " + c("›", "bold", "ouro") + " " + c(rotulo, "bold")
    if dica:
        linha += " " + c("(" + dica + ")", "muted")
    linha += c(": ", "muted")
    print(linha, end="", flush=True)
    try:
        return input().strip()
    except EOFError:
        print()
        raise SystemExit(0)


def pausa():
    print()
    print("  " + c("Pressione ENTER para voltar ao menu…", "muted"), end="", flush=True)
    try:
        input()
    except EOFError:
        print()
        raise SystemExit(0)

def tabela(cabs, linhas, alinhs=None, recuo=2):
    alinhs = alinhs or ["l"] * len(cabs)
    larg = [len(h) for h in cabs]
    for lin in linhas:
        for i, cel in enumerate(lin):
            if tam(str(cel)) > larg[i]:
                larg[i] = tam(str(cel))
    esp = " " * recuo
    cab = esp + c(" " + "  ".join(ajustar(h, larg[i], alinhs[i]) for i, h in enumerate(cabs)) + " ", "cab")
    print(cab)
    for lin in linhas:
        print(esp + " " + "  ".join(ajustar(str(cel), larg[i], alinhs[i]) for i, cel in enumerate(lin)))


def barra(valor, maximo, larg=24, estilo="azul"):
    if maximo <= 0:
        n = 0
    else:
        n = int(round(valor / maximo * larg))
        if valor > 0 and n == 0:
            n = 1
    return c("█" * n, estilo) + c("░" * (larg - n), "muted")


def etiqueta_arv(nome):
    return c(nome, "bold", "bst" if nome == "BST" else "avl")


if __name__ == "__main__":
    print()
    print("  Teste de cores dos auditorios")
    print()
    for cod, nome in (("EST-01", "Auditório do Estúdio · roxo"), ("AUD-01", "Auditório Central · amarelo"),
                      ("MAS-01", "Auditório Masculino · azul"), ("FEM-01", "Auditório Feminino · rosa"),
                      ("FAC-01", "Auditório da Faculdade · verde"), ("REI-01", "Auditório da Reitoria · ciano"),
                      ("IGR-01", "Igreja UNASP · laranja"), ("EXT-01", "Externa · cinza")):
        print("  " + cor_recurso(cod) + "  " + cor_recurso(cod, nome))
    print()
    print("  cores ativas: %s" % ("sim" if ATIVO else "NÃO (terminal sem suporte, saída redirecionada ou NO_COLOR definido)"))
    print()
