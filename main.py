import os
import sys

import cadastro
import visual as v
from tads import Fila, Pilha
from heap import Heap
from carga import (carregar_reservas, gravar_reservas, carregar_na_arvore,
                   carregar_na_arvoreb, GRAU_B, para_minutos, rotulo, hora, prioridade, PRIORIDADES,
                   janela_intervalo, completar_janela)
import malha
import relatorio

PASTA = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(PASTA, "reservas_protec.json")
DURACAO_PADRAO = 60   
FORMATO = "dd/mm/aaaa hh:mm"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


class Sistema:
    def __init__(self):
        self.setor = "ProTec"
        self.base = {}
        self.reservas = []          
        self.bst = carregar_na_arvore([], False)
        self.avl = carregar_na_arvore([], True)
        self.arvb = carregar_na_arvoreb([])   
        self.historico = Pilha()    
        self.espera = []            
        self.sujo = False

    def carregar(self):
        self.reservas, self.base = carregar_reservas(BASE)
        self.setor = self.base.get("setor", self.setor)
        self.reconstruir()
        self.historico = Pilha()
        self.espera = []
        self.sujo = False

    def reconstruir(self):
        self.bst = carregar_na_arvore(self.reservas, balanceada=False)
        self.avl = carregar_na_arvore(self.reservas, balanceada=True)
        self.arvb = carregar_na_arvoreb(self.reservas)

    def salvar(self):
        gravar_reservas(BASE, self.base, self.reservas)
        self.sujo = False

    def recursos(self):
        vistos, saida = [], []
        for r in self.reservas:
            if r["recurso"] not in vistos:
                vistos.append(r["recurso"])
                saida.append((r["recurso"], r["local"]))
        return saida

    def maior_duracao(self):
        maior = DURACAO_PADRAO
        for r in self.reservas:
            if r["duracao"] is not None and r["duracao"] > maior:
                maior = r["duracao"]
        return maior

    def fim_efetivo(self, r):
        return r["fim"] if r["fim"] is not None else r["inicio"] + DURACAO_PADRAO

    def conflitos(self, recurso, ini, fim):
        candidatas, visitados = self.avl.faixa(ini - self.maior_duracao(), fim)
        achadas = []
        for r in candidatas:
            if r["recurso"] == recurso and r["inicio"] < fim and self.fim_efetivo(r) > ini:
                achadas.append(r)
        return achadas, visitados

    def inserir_ordenado(self, nova):
        i = 0
        while i < len(self.reservas) and (self.reservas[i]["inicio"], self.reservas[i]["id"]) <= (nova["inicio"], nova["id"]):
            i += 1
        self.reservas.insert(i, nova)

    def proximo_id(self):
        maior = 0
        for r in self.reservas:
            if r["id"] > maior:
                maior = r["id"]
        return maior + 1

    def nome_recurso(self, cod):
        for c, local in self.recursos():
            if c == cod:
                return v.cor_recurso(c, "%s · %s" % (c, local))
        return cod

    def reserva_por_id(self, id_):
        for r in self.reservas:
            if r["id"] == id_:
                return r
        return None

    def na_espera(self, id_):
        for r in self.espera:
            if r["id"] == id_:
                return True
        return False

    def sair_da_espera(self, id_):
        self.espera = [r for r in self.espera if r["id"] != id_]

    def ordem_fifo(self):
        fila = Fila()
        for r in self.espera:
            fila.enfileirar(r)
        ordem = []
        while not fila.vazia():
            ordem.append(fila.desenfileirar())
        return ordem, fila.operacoes

    def ordem_heap(self):
        h = Heap()
        for r in self.espera:
            h.inserir((prioridade(r), r["id"]), r)
        ordem = []
        while not h.vazia():
            ordem.append(h.remover_topo()[1])
        return ordem, h.comparacoes, h.trocas

    def disputas_da_base(self, mesmo_recurso=True):
        saida = []
        folga = self.maior_duracao()
        for r in self.reservas:
            fim = self.fim_efetivo(r)
            candidatas, _ = self.avl.faixa(r["inicio"] - folga, fim)
            for s in candidatas:
                if s["id"] < r["id"] and s["inicio"] < fim and self.fim_efetivo(s) > r["inicio"] \
                        and (not mesmo_recurso or s["recurso"] == r["recurso"]):
                    saida.append(r)
                    break
        return saida

VOLTAR = object()   

def tela(sis, titulo, passo=None, total=None, resumo=None, destino1="ao menu"):
    v.cabecalho(titulo, sis.setor, passo, total)
    if passo:
        destino = destino1 if passo == 1 else "ao passo anterior"
        print("  " + v.c("‹ digite 0 para voltar %s · vazio cancela" % destino, "muted"))
        print()
    if resumo:
        v.resumo(resumo)


def tabela_reservas(rs):
    larg_desc = max(12, v.largura() - 58)
    linhas = []
    for r in rs:
        fim = hora(r["fim"]) if r["fim"] is not None else v.c("?", "muted")
        ji, jf = janela_intervalo(r)
        janela = "%s-%s" % (hora(ji), hora(jf))
        linhas.append([v.c("#%d" % r["id"], "muted"), rotulo(r["inicio"]), fim, janela,
                       v.cor_recurso(r["recurso"]), v.cortar(r["descricao"], larg_desc)])
    v.tabela(["id", "início", "fim", "janela", "recurso", "descrição"], linhas, ["r", "l", "l", "l", "l", "l"])


def pedir_instante(rotulo_campo):
    while True:
        txt = v.ler(rotulo_campo, FORMATO + " · 0 volta")
        if txt == "0":
            return VOLTAR
        if txt == "":
            return None
        try:
            return para_minutos(txt)
        except ValueError as e:
            v.erro(str(e))


def escolher_recurso(sis):
    recs = sis.recursos()
    v.tabela(["nº", "código", "local"],
             [[v.c(i, "bold", "ouro"), v.cor_recurso(c), v.cor_recurso(c, local)] for i, (c, local) in enumerate(recs, 1)], ["r", "l", "l"])
    print()
    while True:
        txt = v.ler("Recurso", "número · 0 volta · vazio cancela")
        if txt == "0":
            return VOLTAR
        if txt == "":
            return None
        if txt.isdigit() and 1 <= int(txt) <= len(recs):
            return recs[int(txt) - 1][0]
        v.erro("Escolha um número da lista.")


def percorrer(passos):
    valores = []
    i = 0
    while i < len(passos):
        r = passos[i](valores)
        if r is None:
            return None
        if r is VOLTAR:
            if i == 0:
                return VOLTAR
            valores.pop()
            i -= 1
        else:
            valores.append(r)
            i += 1
    return valores


def cancelado(sis):
    v.aviso("Cancelado. Voltando ao menu…")
    v.pausa()

def op_carregar(sis):
    tela(sis, "Carregar base de campo")
    sis.carregar()
    v.ok("Base carregada de %s" % v.c(os.path.basename(BASE), "branco"))
    v.info("%s reservas · %s instantes distintos" % (
        v.c(sis.bst.n_reservas, "bold", "branco"), v.c(sis.bst.n_nos, "bold", "branco")))
    print()
    v.tabela(["árvore", "altura", "coerente"],
             [[v.etiqueta_arv("BST"), sis.bst.altura(), "✔ sim" if sis.bst.coerente() else "✖ não"],
              [v.etiqueta_arv("AVL"), sis.avl.altura(), "✔ sim" if sis.avl.coerente() else "✖ não"]],
             ["l", "r", "l"])
    v.pausa()

def op_registrar(sis):
    T, total = "Registrar pedido de reserva", 5

    def p_rec(vals):
        tela(sis, T, 1, total)
        return escolher_recurso(sis)

    def p_ini(vals):
        tela(sis, T, 2, total, [("Recurso", sis.nome_recurso(vals[0]))])
        while True:
            ini = pedir_instante("Início")
            if ini is None or ini is VOLTAR:
                return ini
            if ini < 0:
                v.erro("O início é antes do começo da série (11/10/2026).")
                continue
            return ini

    def p_fim(vals):
        tela(sis, T, 3, total, [("Recurso", sis.nome_recurso(vals[0])), ("Início", rotulo(vals[1]))])
        while True:
            fim = pedir_instante("Fim")
            if fim is None or fim is VOLTAR:
                return fim
            if fim <= vals[1]:
                v.erro("O fim precisa ser depois do início.")
                continue
            return fim

    def p_desc(vals):
        tela(sis, T, 4, total, [("Recurso", sis.nome_recurso(vals[0])),
                                ("Início", rotulo(vals[1])), ("Fim", rotulo(vals[2]))])
        txt = v.ler("Descrição", "0 volta · vazio cancela")
        if txt == "0":
            return VOLTAR
        return txt or None

    def p_conflito(vals):
        rec, ini, fim = vals[0], vals[1], vals[2]
        achadas, _ = sis.conflitos(rec, ini, fim)
        if not achadas:
            return "confirmada"
        tela(sis, T, 5, total, [("Recurso", sis.nome_recurso(rec)), ("Início", rotulo(ini)), ("Fim", rotulo(fim))])
        v.faixa("CONFLITO DE HORÁRIO", "aviso")
        print()
        v.aviso("O mesmo recurso já está reservado nesse intervalo:")
        print()
        tabela_reservas(achadas)
        print()
        while True:
            r = v.ler("Registrar mesmo assim como em_espera?", "s/n · 0 volta").lower()
            if r == "0":
                return VOLTAR
            if r == "s":
                return "em_espera"
            if r == "n":
                return None   
            v.erro("Digite s, n ou 0 para voltar.")

    vals = percorrer([p_rec, p_ini, p_fim, p_desc, p_conflito])
    if vals is VOLTAR:
        return
    if vals is None:
        return cancelado(sis)
    rec, ini, fim, desc, status = vals
    local = ""
    for cod, loc in sis.recursos():
        if cod == rec:
            local = loc
    nova = {"id": sis.proximo_id(), "recurso": rec, "local": local, "descricao": desc,
            "data": None, "data_fim_periodo": None, "chegada_equipe": None,
            "inicio": ini, "fim": fim, "duracao": fim - ini, "status": status}
    completar_janela(nova)
    sis.inserir_ordenado(nova)
    sis.bst.inserir(ini, nova)
    sis.avl.inserir(ini, nova)
    sis.arvb.inserir(ini, nova)
    sis.historico.empilhar(nova["id"])
    if status == "em_espera":
        sis.espera.append(nova)
    sis.sujo = True
    tela(sis, "Pedido registrado")
    v.ok("Reserva #%d registrada como %s" % (nova["id"], v.c(status, "bold", "ok" if status == "confirmada" else "aviso")))
    print()
    tabela_reservas([nova])
    print()
    v.info("Inserção acumulada: %s %s comparações · %s %s comparações (%d rotações)" % (
        v.etiqueta_arv("BST"), v.c(sis.bst.comparacoes, "bold", "branco"),
        v.etiqueta_arv("AVL"), v.c(sis.avl.comparacoes, "bold", "branco"), sis.avl.rotacoes))
    v.pausa()


def op_agenda(sis):
    T, total = "Agenda por faixa de horário", 3

    def p_de(vals):
        tela(sis, T, 1, total)
        return pedir_instante("De")

    def p_ate(vals):
        tela(sis, T, 2, total, [("De", rotulo(vals[0]))])
        while True:
            fim = pedir_instante("Até")
            if fim is None or fim is VOLTAR:
                return fim
            if fim < vals[0]:
                v.erro("O fim vem antes do início.")
                continue
            return fim

    def p_estrutura(vals):
        tela(sis, T, 3, total, [("De", rotulo(vals[0])), ("Até", rotulo(vals[1]))])
        print("  " + v.c("1", "bold", "ouro") + "  " + v.etiqueta_arv("BST") + v.c("        árvore sem balanceamento", "muted"))
        print("  " + v.c("2", "bold", "ouro") + "  " + v.etiqueta_arv("AVL") + v.c("        árvore balanceada", "muted"))
        print("  " + v.c("3", "bold", "ouro") + "  " + v.c("Varredura", "bold", "branco") + v.c("  passa pela lista inteira", "muted"))
        print()
        txt = v.ler("Estrutura", "1, 2 ou 3 · padrão 2 · 0 volta")
        if txt == "0":
            return VOLTAR
        return txt or "2"

    vals = percorrer([p_de, p_ate, p_estrutura])
    if vals is VOLTAR:
        return
    if vals is None:
        return cancelado(sis)
    ini, fim, esc = vals
    if esc == "1":
        achadas, visitados = sis.bst.faixa(ini, fim)
        nome, estilo, unidade = "BST", "bst", "nós"
    elif esc == "3":
        achadas, visitados = [], 0
        for r in sis.reservas:
            visitados += 1
            if ini <= r["inicio"] <= fim:
                achadas.append(r)
        nome, estilo, unidade = "Varredura", "branco", "registros"
    else:
        achadas, visitados = sis.avl.faixa(ini, fim)
        nome, estilo, unidade = "AVL", "avl", "nós"
    tela(sis, T, resumo=[("Faixa", "%s  →  %s" % (rotulo(ini), rotulo(fim))), ("Estrutura", nome)])
    if achadas:
        tabela_reservas(achadas)
    else:
        v.aviso("Nenhuma reserva começa nessa faixa.")
    print()
    v.info("%s reservas encontradas" % v.c(len(achadas), "bold", "branco"))
    print("  " + v.c(nome, "bold", estilo) + " visitou " + v.c(visitados, "bold", "branco") + " " + unidade
          + v.c("  de %d na base" % sis.bst.n_reservas, "muted"))
    print("  " + v.barra(visitados, sis.bst.n_reservas, 30, "bst" if estilo == "bst" else ("avl" if estilo == "avl" else "muted")))
    v.pausa()


def op_malha(sis):
    T, total = "Malha de trechos do recurso", 2

    def p_rec(vals):
        tela(sis, T, 1, total)
        return escolher_recurso(sis)

    def p_dia(vals):
        tela(sis, T, 2, total, [("Recurso", sis.nome_recurso(vals[0]))])
        while True:
            txt = v.ler("Dia", "dd/mm/aaaa · 0 volta · vazio cancela")
            if txt == "0":
                return VOLTAR
            if txt == "":
                return None
            try:
                return para_minutos(txt + " 00:00") // 1440
            except ValueError:
                v.erro("Use o formato dd/mm/aaaa (ex.: 13/10/2026).")

    vals = percorrer([p_rec, p_dia])
    if vals is VOLTAR:
        return
    if vals is None:
        return cancelado(sis)
    rec, dia = vals
    trechos = malha.malha_dia(sis.reservas, rec, dia)
    res = malha.resumo(trechos)
    tela(sis, T, resumo=[("Recurso", sis.nome_recurso(rec)), ("Dia", rotulo(dia * 1440)[:9]),
                         ("Trecho", "%d min" % malha.PASSO)])
    por_id = {r["id"]: r for r in sis.reservas}
    larg_desc = max(12, v.largura() - 26)
    simbolo = {"uso": v.cor_recurso(rec, "██"), "prep": v.c("▒▒", "aviso"), "livre": v.c("░░", "muted")}
    for i in range(0, len(trechos), 2):
        par = trechos[i:i + 2]
        ids = []
        for t in par:
            for id_ in t["ids"]:
                if id_ not in ids:
                    ids.append(id_)
        txt = "  ".join("#%d %s" % (k, por_id[k]["descricao"]) for k in ids)
        print("  " + v.c(hora(par[0]["de"]), "muted") + "  " + " ".join(simbolo[t["estado"]] for t in par)
              + "  " + v.cortar(txt, larg_desc))
    print()
    print("  " + simbolo["uso"] + " em uso   " + simbolo["prep"] + " preparo da equipe   "
          + simbolo["livre"] + " livre")
    print()
    v.info("%s trechos livres · %s em uso · %s em preparo · ocupação %s" % (
        v.c(res["livre"], "bold", "ok"), v.c(res["uso"], "bold", "branco"),
        v.c(res["prep"], "bold", "aviso"), v.c("%.0f%%" % res["ocupacao"], "bold", "branco")))
    v.info("Reservas em espera não ocupam a malha.")
    v.pausa()


def op_disponibilidade(sis):
    T, total = "Disponibilidade de um recurso", 3

    def p_rec(vals):
        tela(sis, T, 1, total)
        return escolher_recurso(sis)

    def p_de(vals):
        tela(sis, T, 2, total, [("Recurso", sis.nome_recurso(vals[0]))])
        return pedir_instante("De")

    def p_ate(vals):
        tela(sis, T, 3, total, [("Recurso", sis.nome_recurso(vals[0])), ("De", rotulo(vals[1]))])
        while True:
            fim = pedir_instante("Até")
            if fim is None or fim is VOLTAR:
                return fim
            if fim <= vals[1]:
                v.erro("O fim precisa ser depois do início.")
                continue
            return fim

    vals = percorrer([p_rec, p_de, p_ate])
    if vals is VOLTAR:
        return
    if vals is None:
        return cancelado(sis)
    rec, ini, fim = vals
    tela(sis, T, resumo=[("Recurso", sis.nome_recurso(rec)),
                         ("Intervalo", "%s  →  %s" % (rotulo(ini), rotulo(fim)))])
    achadas, visitados = sis.conflitos(rec, ini, fim)
    if not achadas:
        v.faixa("LIVRE", "ok")
        print()
        v.ok("Nenhuma reserva ocupa o recurso nesse intervalo.")
    else:
        v.faixa("OCUPADO", "erro")
        print()
        tabela_reservas(achadas)
    print()
    v.info("AVL visitou %s nós. Reservas sem hora de fim contam %d min." % (v.c(visitados, "bold", "branco"), DURACAO_PADRAO))
    v.pausa()

def _cel_pedido(r, larg=24):
    return "%s %s %s" % (v.c("#%d" % r["id"], "muted"), v.c("P%d" % prioridade(r), "bold", "ouro"),
                         v.cortar(r["descricao"], larg))


def _mostrar_espera(sis, limite=8):
    if not sis.espera:
        v.aviso("A lista de espera está vazia. Use a opção 1 ou 2 para colocar pedidos nela.")
        return
    v.info("%s pedidos na lista, em ordem de chegada" % v.c(len(sis.espera), "bold", "branco"))
    print()
    linhas = []
    for i, r in enumerate(sis.espera[:limite], 1):
        linhas.append([v.c(i, "muted"), v.c("#%d" % r["id"], "muted"), "P%d" % prioridade(r),
                       v.cor_recurso(r["recurso"]), v.cortar(r["descricao"], max(16, v.largura() - 40))])
    v.tabela(["nº", "id", "prio", "recurso", "descrição"], linhas, ["r", "r", "l", "l", "l"])
    if len(sis.espera) > limite:
        print("  " + v.c("… e mais %d" % (len(sis.espera) - limite), "muted"))


def _espera_disputas(sis):
    tela(sis, "Disputas da base")
    print("  " + v.c("1", "bold", "ouro") + "  " + v.c("Mesmo recurso", "bold", "branco") + v.c("     horários que se sobrepõem no mesmo auditório", "muted"))
    print("  " + v.c("2", "bold", "ouro") + "  " + v.c("Qualquer recurso", "bold", "branco") + v.c("  horários que se sobrepõem e disputam a mesma equipe", "muted"))
    print()
    while True:
        esc = v.ler("Tipo de disputa", "1 ou 2 · 0 volta")
        if esc in ("0", "1", "2"):
            break
        v.erro("Digite 1, 2 ou 0.")
    if esc == "0":
        return
    tela(sis, "Disputas da base")
    novas = 0
    for r in sis.disputas_da_base(esc == "1"):
        if not sis.na_espera(r["id"]):
            sis.espera.append(r)
            novas += 1
    v.ok("%s pedidos entraram na lista de espera" % v.c(novas, "bold", "branco"))
    print()
    v.info("São os pedidos que se sobrepõem a um pedido de id menor (que chegou antes).")
    v.info("Simulação: a base de campo não traz o status de cada pedido.")
    v.pausa()


def _espera_adicionar(sis):
    T = "Adicionar à lista de espera"

    def p_id(vals):
        tela(sis, T, 1, 2, destino1="à lista de espera")
        while True:
            txt = v.ler("Id da reserva", "0 volta · vazio cancela")
            if txt == "0":
                return VOLTAR
            if txt == "":
                return None
            if not txt.isdigit():
                v.erro("Digite o número do id.")
                continue
            r = sis.reserva_por_id(int(txt))
            if r is None:
                v.erro("Não existe reserva com esse id.")
            elif sis.na_espera(r["id"]):
                v.erro("Essa reserva já está na lista.")
            else:
                return r

    def p_conf(vals):
        r = vals[0]
        tela(sis, T, 2, 2)
        tabela_reservas([r])
        print()
        v.info("Prioridade %s · %s" % (v.c(prioridade(r), "bold", "ouro"), PRIORIDADES[prioridade(r)]))
        print()
        while True:
            txt = v.ler("Adicionar à lista?", "s/n · 0 volta").lower()
            if txt == "0":
                return VOLTAR
            if txt == "s":
                return True
            if txt == "n":
                return None
            v.erro("Digite s, n ou 0 para voltar.")

    vals = percorrer([p_id, p_conf])
    if vals is VOLTAR:
        return
    if vals is None:
        v.aviso("Nada foi adicionado.")
        return v.pausa()
    sis.espera.append(vals[0])
    tela(sis, T)
    v.ok("Reserva #%d entrou na lista de espera" % vals[0]["id"])
    v.pausa()


def _espera_comparar(sis, limite=12):
    tela(sis, "Fila FIFO × Heap de prioridade")
    if not sis.espera:
        v.aviso("A lista de espera está vazia.")
        return v.pausa()
    fifo, ops = sis.ordem_fifo()
    heap, comps, trocas = sis.ordem_heap()
    n = len(fifo)
    linhas = [[v.c(i + 1, "muted"), _cel_pedido(fifo[i]), _cel_pedido(heap[i])] for i in range(min(n, limite))]
    v.tabela(["nº", "Fila FIFO (chegada)", "Heap (prioridade)"], linhas, ["r", "l", "l"])
    if n > limite:
        print("  " + v.c("… e mais %d" % (n - limite), "muted"))
    print()
    print("  " + v.c("FIFO", "bold", "branco") + " chama primeiro  " + _cel_pedido(fifo[0], 40))
    print("  " + v.c("Heap", "bold", "ouro") + " chama primeiro  " + _cel_pedido(heap[0], 40))
    print()
    v.info("Fila: %s operações · Heap: %s comparações e %s trocas" % (
        v.c(ops, "bold", "branco"), v.c(comps, "bold", "branco"), v.c(trocas, "bold", "branco")))
    v.info("P1 é a prioridade mais alta; em empate, sai quem chegou primeiro.")
    v.pausa()


def _espera_chamar(sis):
    tela(sis, "Chamar o próximo da lista")
    if not sis.espera:
        v.aviso("A lista de espera está vazia.")
        return v.pausa()
    print("  " + v.c("1", "bold", "ouro") + "  " + v.c("Fila FIFO", "bold", "branco") + v.c("   quem chegou primeiro", "muted"))
    print("  " + v.c("2", "bold", "ouro") + "  " + v.c("Heap", "bold", "branco") + v.c("        quem tem maior prioridade", "muted"))
    print()
    while True:
        esc = v.ler("Estrutura", "1 ou 2 · 0 volta")
        if esc in ("0", "1", "2"):
            break
        v.erro("Digite 1, 2 ou 0.")
    if esc == "0":
        return
    fifo, _ = sis.ordem_fifo()
    heap, _, _ = sis.ordem_heap()
    escolhido, outro, nome, outro_nome = (fifo[0], heap[0], "FIFO", "Heap") if esc == "1" else (heap[0], fifo[0], "Heap", "FIFO")
    sis.sair_da_espera(escolhido["id"])
    tela(sis, "Próximo chamado")
    v.ok("%s chamou o pedido #%d" % (v.c(nome, "bold", "branco"), escolhido["id"]))
    print()
    tabela_reservas([escolhido])
    print()
    if outro["id"] == escolhido["id"]:
        v.info("A outra versão (%s) chamaria o mesmo pedido." % outro_nome)
    else:
        v.info("A outra versão (%s) chamaria o #%d (prioridade %d)." % (outro_nome, outro["id"], prioridade(outro)))
    v.info("Restam %s pedidos na lista." % v.c(len(sis.espera), "bold", "branco"))
    v.pausa()


def op_espera(sis):
    T = "Lista de espera"
    msg = None
    while True:
        tela(sis, T)
        _mostrar_espera(sis)
        print()
        for cod, txt in (("1", "Montar a lista com as disputas da base"), ("2", "Adicionar uma reserva à lista"),
                         ("3", "Comparar a ordem de saída: Fila FIFO × Heap"), ("4", "Chamar o próximo"),
                         ("0", "Voltar ao menu")):
            print("  " + v.c(cod, "bold", "ouro") + "  " + v.c(txt, "branco"))
        print()
        if msg:
            v.erro(msg)
            msg = None
        esc = v.ler("Opção")
        if esc == "0":
            return
        elif esc == "1":
            _espera_disputas(sis)
        elif esc == "2":
            _espera_adicionar(sis)
        elif esc == "3":
            _espera_comparar(sis)
        elif esc == "4":
            _espera_chamar(sis)
        else:
            msg = "Opção inválida. Digite 0, 1, 2, 3 ou 4."


def op_desfazer(sis):
    tela(sis, "Desfazer a última operação")
    if sis.historico.vazia():
        v.aviso("Não há nada para desfazer nesta sessão.")
        return v.pausa()
    id_ = sis.historico.desempilhar()
    removida = None
    for i in range(len(sis.reservas)):
        if sis.reservas[i]["id"] == id_:
            removida = sis.reservas[i]
            del sis.reservas[i]
            break
    sis.reconstruir()
    sis.sair_da_espera(id_)
    sis.sujo = True
    v.ok("Reserva #%d removida" % id_)
    print()
    tabela_reservas([removida])
    print()
    v.info("Árvores reconstruídas com %s reservas." % v.c(sis.bst.n_reservas, "bold", "branco"))
    v.pausa()


def op_indice_disco(sis):
    T = "Índice em disco do histórico"
    msg = None
    while True:
        tela(sis, T)
        b = sis.arvb
        v.info("Árvore B de grau mínimo %d (até %d chaves por página) · %s chaves · %s páginas · altura %s" % (
            b.t, 2 * b.t - 1, v.c(b.n_chaves, "bold", "branco"), v.c(b.n_paginas, "bold", "branco"),
            v.c(b.altura(), "bold", "branco")))
        v.info("Ocupação média das páginas: %.0f%% · coerente: %s" % (
            b.ocupacao(), "✔ sim" if b.coerente() else "✖ não"))
        print()
        for cod, txt in (("1", "Buscar um instante exato"), ("2", "Consultar uma faixa de horário"),
                         ("3", "Comparar com a AVL (páginas lidas × nós visitados)"), ("0", "Voltar ao menu")):
            print("  " + v.c(cod, "bold", "ouro") + "  " + v.c(txt, "branco"))
        print()
        if msg:
            v.erro(msg)
            msg = None
        esc = v.ler("Opção")
        if esc == "0":
            return
        if esc == "1":
            ini = pedir_instante("Instante")
            if ini is None or ini is VOLTAR:
                continue
            achadas, lidas = b.buscar(ini)
            _, nos = sis.avl.buscar(ini)
            tela(sis, T, resumo=[("Instante", rotulo(ini))])
            if achadas:
                tabela_reservas(achadas)
            else:
                v.aviso("Nenhuma reserva começa nesse instante.")
            print()
            v.info("Árvore B leu %s páginas · AVL visitou %s nós" % (
                v.c(lidas, "bold", "branco"), v.c(nos, "bold", "branco")))
            v.pausa()
        elif esc == "2":
            ini = pedir_instante("De")
            if ini is None or ini is VOLTAR:
                continue
            fim = pedir_instante("Até")
            if fim is None or fim is VOLTAR:
                continue
            if fim < ini:
                msg = "O fim vem antes do início."
                continue
            achadas, lidas = b.faixa(ini, fim)
            _, nos = sis.avl.faixa(ini, fim)
            tela(sis, T, resumo=[("Faixa", "%s  →  %s" % (rotulo(ini), rotulo(fim)))])
            if achadas:
                tabela_reservas(achadas)
            else:
                v.aviso("Nenhuma reserva começa nessa faixa.")
            print()
            v.info("%s reservas · árvore B leu %s páginas · AVL visitou %s nós" % (
                v.c(len(achadas), "bold", "branco"), v.c(lidas, "bold", "branco"), v.c(nos, "bold", "branco")))
            v.pausa()
        elif esc == "3":
            tela(sis, "Árvore B × AVL")
            relatorio.mostrar_a3(sis.reservas, sis.avl)
            v.pausa()
        else:
            msg = "Opção inválida. Digite 0, 1, 2 ou 3."


def op_desempenho(sis):
    tela(sis, "Desempenho das estruturas")
    relatorio.mostrar_relatorio(sis.reservas, sis.bst, sis.avl)
    v.pausa()


def op_gravar(sis):
    tela(sis, "Gravar relatório em arquivo")
    caminho = os.path.join(PASTA, "relatorio.txt")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(relatorio.texto_relatorio(sis.setor, sis.reservas, sis.bst, sis.avl) + "\n")
    v.ok("Relatório gravado em %s" % v.c(caminho, "branco"))
    v.pausa()


def em_breve(titulo, texto):
    def f(sis):
        tela(sis, titulo)
        v.faixa("EM BREVE", "aviso")
        print()
        v.aviso(texto)
        v.pausa()
    return f

def op_cadastro(sis):
    cadastro.menu()


MENU = [
    ("1", "Carregar base de campo", "", None, op_carregar),
    ("2", "Cadastrar / editar / remover recurso", "inventário de recursos", None, op_cadastro),
    ("3", "Registrar pedido de reserva", "", None, op_registrar),
    ("4", "Agenda por faixa de horário", "", None, op_agenda),
    ("5", "Consultar disponibilidade de um recurso", "", None, op_disponibilidade),
    ("6", "Lista de espera", "", None, op_espera),
    ("7", "Desfazer a última operação", "", None, op_desfazer),
    ("8", "Índice em disco do histórico", "", None, op_indice_disco),
    ("9", "Relatório de desempenho das estruturas", "", None, op_desempenho),
    ("10", "Conflito de deslocamento", "extensão B", "",
     em_breve("Conflito de deslocamento", "Trilha B (trajetoria.py) ainda não iniciada.")),
    ("11", "Gravar relatório em arquivo", "relatorio.txt", None, op_gravar),
    ("12", "Malha de trechos do recurso", "grade do dia por janela", None, op_malha),
    ("0", "Sair", "", None, None),
]


def mostrar_menu(sis, mensagem=None):
    tela(sis, "Menu principal")
    for cod, texto, detalhe, futura, _ in MENU:
        num = v.c(v.ajustar(cod, 2, "r"), "bold", "ouro" if futura is None else "muted")
        if futura is None:
            linha = "  %s   %s" % (num, v.c(texto, "branco"))
            if detalhe:
                linha += "  " + v.c(detalhe, "muted")
        else:
            linha = "  %s   %s" % (num, v.c(texto, "muted"))
        print(linha)
    print()
    print(v.c("  " + "─" * (v.largura() - 4), "muted"))
    print("  %s %s reservas · %s altura %s · %s altura %s" % (
        v.c("base", "muted"), v.c(sis.bst.n_reservas, "bold", "branco"),
        v.etiqueta_arv("BST"), v.c(sis.bst.altura(), "bold", "branco"),
        v.etiqueta_arv("AVL"), v.c(sis.avl.altura(), "bold", "branco")))
    if sis.sujo:
        print("  " + v.c("▲ alterações ainda não gravadas na base", "aviso"))
    print()
    if mensagem:
        v.erro(mensagem)


def sair(sis):
    if sis.sujo:
        tela(sis, "Sair")
        v.aviso("Há alterações que ainda não foram gravadas na base.")
        print()
        if v.ler("Gravar na base antes de sair?", "s/n").lower() == "s":
            sis.salvar()
    v.limpar()
    print(v.c("  Até logo.", "ouro"))


def principal():
    sis = Sistema()
    mensagem = None
    try:
        sis.carregar()
    except (OSError, ValueError, KeyError) as e:
        mensagem = "Não foi possível carregar a base (%s). Corrija e use a opção 1." % e
    while True:
        mostrar_menu(sis, mensagem)
        mensagem = None
        esc = v.ler("Opção")
        if esc == "0":
            return sair(sis)
        acao = None
        for cod, _, _, _, fn in MENU:
            if cod == esc:
                acao = fn
        if acao is None:
            mensagem = "Opção inválida. Digite um número do menu."
            continue
        try:
            acao(sis)
        except (OSError, ValueError, KeyError) as e:
            tela(sis, "Erro")
            v.erro(str(e))
            v.pausa()


if __name__ == "__main__":
    sys.exit(principal())