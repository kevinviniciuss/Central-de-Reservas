import math
import visual as v
from carga import carregar_na_arvore, carregar_na_arvoreb, rotulo, prioridade
from heap import heapsort, k_menores_com_heap


def medir(reservas, balanceada):
    arv = carregar_na_arvore(reservas, balanceada)
    return {
        "reservas": arv.n_reservas,
        "nos": arv.n_nos,
        "altura": arv.altura(),
        "comparacoes": arv.comparacoes,
        "caminho_medio": arv.caminho_medio(),
        "rotacoes": arv.rotacoes,
        "coerente": arv.coerente(),
    }, arv


def tabela_a1(reservas):
    n = len(reservas)
    linhas = []
    for nome, k in (("1/3", n // 3), ("2/3", 2 * n // 3), ("total", n)):
        if k == 0:
            continue
        sub = reservas[:k]
        mb, _ = medir(sub, False)
        ma, _ = medir(sub, True)
        linhas.append((nome, k, mb, ma))
    return linhas


def tabela_a2(reservas, bst, avl):
    ultimo = reservas[-1]["inicio"] // 1440
    contagem = [0] * (ultimo + 1)
    for r in reservas:
        contagem[r["inicio"] // 1440] += 1
    cheio = calmo = primeiro = -1
    for dia in range(len(contagem)):
        if contagem[dia] == 0:
            continue
        if primeiro < 0:
            primeiro = dia
        if cheio < 0 or contagem[dia] > contagem[cheio]:
            cheio = dia
        if calmo < 0 or contagem[dia] < contagem[calmo]:
            calmo = dia
    faixas = (("dia mais movimentado", cheio, cheio),
              ("dia mais calmo", calmo, calmo),
              ("primeira semana", primeiro, primeiro + 6),
              ("base inteira", 0, ultimo))
    linhas = []
    for nome, d1, d2 in faixas:
        ini, fim = d1 * 1440, d2 * 1440 + 1439
        achadas_b, nos_b = bst.faixa(ini, fim)
        achadas_a, nos_a = avl.faixa(ini, fim)
        linhas.append((nome, rotulo(ini)[:9], len(achadas_a), nos_b, nos_a, len(reservas)))
    return linhas


def tabela_a4(reservas):
    itens = [((prioridade(r), r["id"]), r) for r in reservas]
    chave = lambda it: it[0]
    _, comp_todos, _ = heapsort(itens, chave)
    linhas = []
    for k in (1, 5, 10, 20):
        if k <= len(itens):
            _, comp_k, _ = k_menores_com_heap(itens, k, chave)
            linhas.append((k, comp_k, comp_todos))
    primeiro_fifo = reservas[0]
    for r in reservas:
        if r["id"] < primeiro_fifo["id"]:
            primeiro_fifo = r
    primeiro_heap = k_menores_com_heap(itens, 1, chave)[0][0][1]
    return {"n": len(itens), "linhas": linhas, "todos": comp_todos,
            "fifo": (primeiro_fifo["id"], prioridade(primeiro_fifo), primeiro_fifo["descricao"]),
            "heap": (primeiro_heap["id"], prioridade(primeiro_heap), primeiro_heap["descricao"])}


def tabela_a3(reservas, avl):
    chaves = [c for c, _ in avl.em_ordem_com_pilha()]
    contagem = {}
    for rv in reservas:
        d = rv["inicio"] // 1440
        contagem[d] = contagem.get(d, 0) + 1
    cheio = None
    for d in contagem:
        if cheio is None or contagem[d] > contagem[cheio]:
            cheio = d
    f_dia = (cheio * 1440, cheio * 1440 + 1439)
    f_tudo = (0, chaves[-1])
    _, nos_dia = avl.faixa(*f_dia)
    _, nos_tudo = avl.faixa(*f_tudo)
    linhas = [("AVL", "-", avl.altura(), avl.n_nos, avl.caminho_medio(), nos_dia, nos_tudo, None, None)]
    for t in (2, 3, 5, 10):
        b = carregar_na_arvoreb(reservas, t)
        soma = 0
        for ch in chaves:
            soma += b.buscar(ch)[1]
        _, p_dia = b.faixa(*f_dia)
        _, p_tudo = b.faixa(*f_tudo)
        linhas.append(("B", t, b.altura(), b.n_paginas, soma / len(chaves), p_dia, p_tudo,
                       b.escritas, b.coerente()))
    return linhas


def mostrar_a3(reservas, avl):
    linhas = tabela_a3(reservas, avl)
    v.secao("Achado A3 · índice em disco (leituras de página)")
    maxl = max(l[4] for l in linhas)
    v.tabela(["estrutura", "t", "altura", "páginas", "leit./busca", "", "faixa dia", "faixa base"],
             [[v.etiqueta_arv("AVL") if e == "AVL" else v.c("B", "bold", "ouro"), t, alt, pg, "%.2f" % med,
               v.barra(med, maxl, 10, "avl" if e == "AVL" else "ouro"), fd, ft]
              for e, t, alt, pg, med, fd, ft, _, _ in linhas],
             ["l", "r", "r", "r", "r", "l", "r", "r"])
    print()
    v.info("AVL: 1 nó = 1 página. Árvore B: cada página guarda até 2t-1 chaves.")
    v.info("Menos níveis = menos leituras de disco por consulta.")


def dados(reservas, bst, avl):
    if bst.n_nos == 0:
        return None
    chaves = [c for c, _ in bst.em_ordem_com_pilha()]
    atual = []
    for rot, a in (("BST", bst), ("AVL", avl)):
        atual.append({"arv": rot, "altura": a.altura(), "comparacoes": a.comparacoes,
                      "caminho_medio": a.caminho_medio(), "rotacoes": a.rotacoes,
                      "coerente": a.coerente()})
    alvos = (("primeira chave", chaves[0]), ("chave do meio", chaves[len(chaves) // 2]),
             ("última chave", chaves[-1]), ("inexistente", chaves[-1] + 1))
    busca = [(nome, rotulo(ch), bst.buscar(ch)[1], avl.buscar(ch)[1]) for nome, ch in alvos]
    return {
        "reservas": bst.n_reservas, "nos": bst.n_nos, "atual": atual,
        "minimo": math.ceil(math.log2(bst.n_nos + 1)),
        "niveis_bst": [len(x) for x in bst.em_largura_com_fila()],
        "niveis_avl": [len(x) for x in avl.em_largura_com_fila()],
        "a1": tabela_a1(reservas), "busca": busca,
        "a2": tabela_a2(reservas, bst, avl), "a3": tabela_a3(reservas, avl), "a4": tabela_a4(reservas),
    }

def texto_relatorio(setor, reservas, bst, avl):
    d = dados(reservas, bst, avl)
    L = ["CENTRAL DE RESERVAS - setor %s" % setor, "=" * 60]
    if d is None:
        return "\n".join(L + ["(base vazia)"])
    L.append("Reservas na base: %d | instantes distintos (nós): %d" % (d["reservas"], d["nos"]))
    L += ["", "ESTADO ATUAL DAS ÁRVORES (carga em ordem cronológica)",
          "%-4s %7s %14s %13s %9s %10s" % ("arv", "altura", "comp.inserção", "caminho_médio", "rotações", "coerente")]
    for a in d["atual"]:
        L.append("%-4s %7d %14d %13.2f %9d %10s" % (a["arv"], a["altura"], a["comparacoes"],
                                                    a["caminho_medio"], a["rotacoes"], a["coerente"]))
    L.append("Altura mínima teórica para n = %d: %d" % (d["nos"], d["minimo"]))
    L.append("Percurso em largura: BST %d níveis (máximo %d nó por nível) | AVL %d níveis %s" % (
        len(d["niveis_bst"]), max(d["niveis_bst"]), len(d["niveis_avl"]), d["niveis_avl"]))
    L += ["", "ACHADO A1 - DEGENERAÇÃO (tabela 1)",
          "%-10s %-4s %7s %14s %13s %9s %6s" % ("base", "arv", "altura", "comp.inserção", "caminho_médio", "rotações", "nós")]
    for nome, k, mb, ma in d["a1"]:
        for rot, m in (("BST", mb), ("AVL", ma)):
            L.append("%-10s %-4s %7d %14d %13.2f %9d %6d" % ("%s (%d)" % (nome, k), rot, m["altura"],
                     m["comparacoes"], m["caminho_medio"], m["rotacoes"], m["nos"]))
    L += ["", "CUSTO DA BUSCA (comparações para localizar a chave)",
          "%-16s %-18s %5s %5s" % ("consulta", "instante", "BST", "AVL")]
    for nome, inst, cb, ca in d["busca"]:
        L.append("%-16s %-18s %5d %5d" % (nome, inst, cb, ca))
    L += ["", "ACHADO A2 - FAIXA CONTRA VARREDURA (nós visitados)",
          "%-22s %-10s %9s %5s %5s %10s" % ("faixa", "a partir de", "achadas", "BST", "AVL", "varredura")]
    for nome, ini, n, nb, na, nv in d["a2"]:
        L.append("%-22s %-10s %9d %5d %5d %10d" % (nome, ini, n, nb, na, nv))
    L += ["", "ACHADO A3 - ÍNDICE EM DISCO (leituras de página; AVL: 1 nó = 1 página)",
          "%-5s %3s %7s %8s %12s %10s %11s" % ("estr.", "t", "altura", "páginas", "leit./busca", "faixa dia", "faixa base")]
    for e, t, alt, pg, med, fd, ft, _, _ in d["a3"]:
        L.append("%-5s %3s %7d %8d %12.2f %10d %11d" % (e, t, alt, pg, med, fd, ft))
    a4 = d["a4"]
    L += ["", "ACHADO A4 - PRIORIDADE (comparações; %d pedidos)" % a4["n"],
          "%-4s %16s %20s %8s" % ("k", "heap (k menores)", "heapsort (ordena tudo)", "heap/tudo")]
    for k, ch, ct in a4["linhas"]:
        L.append("%-4d %16d %20d %7.0f%%" % (k, ch, ct, 100.0 * ch / ct))
    L.append("Primeiro a sair - Fila FIFO: #%d (prioridade %d) %s" % a4["fifo"])
    L.append("Primeiro a sair - Heap:      #%d (prioridade %d) %s" % a4["heap"])
    return "\n".join(L)

def _sim(b):
    return v.c("✔ sim", "ok") if b else v.c("✖ não", "erro")


def mostrar_relatorio(reservas, bst, avl):
    d = dados(reservas, bst, avl)
    if d is None:
        v.aviso("A base está vazia. Carregue a base (opção 1) ou registre reservas.")
        return
    v.info("%s reservas · %s instantes distintos (nós em cada árvore)" % (
        v.c(d["reservas"], "bold", "branco"), v.c(d["nos"], "bold", "branco")))

    v.secao("Estado atual das árvores")
    v.tabela(["árvore", "altura", "comp. inserção", "caminho médio", "rotações", "coerente"],
             [[v.etiqueta_arv(a["arv"]), a["altura"], a["comparacoes"], "%.2f" % a["caminho_medio"],
               a["rotacoes"], _sim(a["coerente"])] for a in d["atual"]],
             ["l", "r", "r", "r", "r", "l"])
    print("  " + v.c("Altura mínima teórica para %d nós: %d" % (d["nos"], d["minimo"]), "muted"))

    v.secao("Forma da árvore (percurso em largura)")
    mx = len(d["niveis_bst"])
    print("  %s  %s  %s" % (v.etiqueta_arv("BST"), v.barra(len(d["niveis_bst"]), mx, 30, "bst"),
                            "%d níveis, no máximo %d nó por nível" % (len(d["niveis_bst"]), max(d["niveis_bst"]))))
    print("  %s  %s  %s" % (v.etiqueta_arv("AVL"), v.barra(len(d["niveis_avl"]), mx, 30, "avl"),
                            "%d níveis" % len(d["niveis_avl"])))
    print()
    mxn = max(d["niveis_avl"])
    for i, n in enumerate(d["niveis_avl"]):
        print("  " + v.c("nível %d" % (i + 1), "muted") + "  " + v.barra(n, mxn, 32, "avl") + " " + str(n) + " nós")

    v.secao("Achado A1 · degeneração (tabela 1)")
    maxc = 1
    for _, _, mb, ma in d["a1"]:
        maxc = max(maxc, mb["comparacoes"], ma["comparacoes"])
    linhas = []
    for nome, k, mb, ma in d["a1"]:
        for rot, m, est in (("BST", mb, "bst"), ("AVL", ma, "avl")):
            linhas.append(["%s (%d)" % (nome, k) if rot == "BST" else "", v.etiqueta_arv(rot), m["altura"],
                           m["comparacoes"], v.barra(m["comparacoes"], maxc, 10, est),
                           "%.2f" % m["caminho_medio"], m["rotacoes"]])
    v.tabela(["base", "árvore", "altura", "comp. inserção", "", "cam. médio", "rotações"], linhas,
             ["l", "l", "r", "r", "l", "r", "r"])

    v.secao("Custo da busca (comparações para localizar a chave)")
    v.tabela(["consulta", "instante", "BST", "AVL"],
             [[nome, inst, v.c(cb, "bst"), v.c(ca, "avl")] for nome, inst, cb, ca in d["busca"]],
             ["l", "l", "r", "r"])

    v.secao("Achado A2 · faixa contra varredura (nós visitados)")
    maxv = d["a2"][0][5]
    v.tabela(["faixa", "a partir de", "achadas", "BST", "AVL", "varredura", ""],
             [[nome, ini, n, v.c(nb, "bst"), v.c(na, "avl"), nv, v.barra(na, maxv, 10, "avl")]
              for nome, ini, n, nb, na, nv in d["a2"]],
             ["l", "l", "r", "r", "r", "r", "l"])

    mostrar_a3(reservas, avl)

    a4 = d["a4"]
    v.secao("Achado A4 · prioridade (comparações, %d pedidos)" % a4["n"])
    v.tabela(["k", "heap (k menores)", "heapsort (tudo)", "heap / tudo"],
             [[k, ch, ct, "%.0f%%" % (100.0 * ch / ct)] for k, ch, ct in a4["linhas"]],
             ["r", "r", "r", "r"])
    print()
    print("  " + v.c("Fila FIFO", "bold", "branco") + " chama primeiro  #%d  prioridade %d  %s" % a4["fifo"])
    print("  " + v.c("Heap", "bold", "ouro") + "      chama primeiro  #%d  prioridade %d  %s" % a4["heap"])
    print()
    v.info("A primeira chave custa pouco na BST, porque é a raiz.")
    v.info("Na AVL, as rotações a empurraram para baixo.")