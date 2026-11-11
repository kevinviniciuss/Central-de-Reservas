class Pagina:
    __slots__ = ("chaves", "reservas", "filhos", "folha")

    def __init__(self, folha):
        self.chaves = []      
        self.reservas = []    
        self.filhos = []      
        self.folha = folha


class ArvoreB:
    def __init__(self, t=3):
        if t < 2:
            raise ValueError("grau minimo t deve ser >= 2")
        self.t = t
        self.raiz = Pagina(True)
        self.n_chaves = 0         
        self.n_reservas = 0       
        self.n_paginas = 1
        self.comparacoes = 0
        self.leituras = 0
        self.escritas = 0
        self.divisoes = 0

    def _posicao(self, pg, chave):
        i = 0
        n = len(pg.chaves)
        while i < n:
            self.comparacoes += 1
            if chave > pg.chaves[i]:
                i += 1
            else:
                break
        return i

    def buscar(self, chave):
        pg = self.raiz
        lidas = 0
        while True:
            lidas += 1
            self.leituras += 1
            i = self._posicao(pg, chave)
            if i < len(pg.chaves) and pg.chaves[i] == chave:
                return pg.reservas[i], lidas
            if pg.folha:
                return [], lidas
            pg = pg.filhos[i]

    def faixa(self, inicio, fim):
        saida = []
        lidas = [0]
        self._faixa(self.raiz, inicio, fim, saida, lidas)
        return saida, lidas[0]

    def _faixa(self, pg, inicio, fim, saida, lidas):
        lidas[0] += 1
        self.leituras += 1
        n = len(pg.chaves)
        i = 0
        while i < n and pg.chaves[i] < inicio:
            i += 1
        while i < n:
            if not pg.folha:
                self._faixa(pg.filhos[i], inicio, fim, saida, lidas)
            if pg.chaves[i] > fim:
                return
            saida.extend(pg.reservas[i])
            i += 1
        if not pg.folha:
            self._faixa(pg.filhos[n], inicio, fim, saida, lidas)

    def inserir(self, chave, reserva):
        self.n_reservas += 1
        existente = self._achar_e_anexar(chave, reserva)
        if existente:
            return
        raiz = self.raiz
        if len(raiz.chaves) == 2 * self.t - 1:
            nova = Pagina(False)
            nova.filhos.append(raiz)
            self.raiz = nova
            self.n_paginas += 1
            self._dividir(nova, 0)
            self._inserir_nao_cheia(nova, chave, reserva)
        else:
            self._inserir_nao_cheia(raiz, chave, reserva)
        self.n_chaves += 1

    def _achar_e_anexar(self, chave, reserva):
        pg = self.raiz
        while True:
            self.leituras += 1
            i = self._posicao(pg, chave)
            if i < len(pg.chaves) and pg.chaves[i] == chave:
                pg.reservas[i].append(reserva)
                self.escritas += 1
                return True
            if pg.folha:
                return False
            pg = pg.filhos[i]

    def _dividir(self, pai, i):
        t = self.t
        filho = pai.filhos[i]
        irmao = Pagina(filho.folha)
        mediana_c = filho.chaves[t - 1]
        mediana_r = filho.reservas[t - 1]
        irmao.chaves = filho.chaves[t:]
        irmao.reservas = filho.reservas[t:]
        filho.chaves = filho.chaves[:t - 1]
        filho.reservas = filho.reservas[:t - 1]
        if not filho.folha:
            irmao.filhos = filho.filhos[t:]
            filho.filhos = filho.filhos[:t]
        pai.chaves.insert(i, mediana_c)
        pai.reservas.insert(i, mediana_r)
        pai.filhos.insert(i + 1, irmao)
        self.n_paginas += 1
        self.divisoes += 1
        self.escritas += 3

    def _inserir_nao_cheia(self, pg, chave, reserva):
        while True:
            self.leituras += 1
            i = self._posicao(pg, chave)
            if pg.folha:
                pg.chaves.insert(i, chave)
                pg.reservas.insert(i, [reserva])
                self.escritas += 1
                return
            if len(pg.filhos[i].chaves) == 2 * self.t - 1:
                self._dividir(pg, i)
                self.comparacoes += 1
                if chave > pg.chaves[i]:
                    i += 1
            pg = pg.filhos[i]

    def altura(self):
        if self.n_chaves == 0:
            return 0
        h, pg = 1, self.raiz
        while not pg.folha:
            pg = pg.filhos[0]
            h += 1
        return h

    def ocupacao(self):
        if self.n_paginas == 0:
            return 0.0
        return 100.0 * self.n_chaves / (self.n_paginas * (2 * self.t - 1))

    def em_ordem(self):
        saida = []
        pilha = [[self.raiz, 0]]
        while pilha:
            quadro = pilha[-1]
            pg, j = quadro
            if pg.folha:
                for k in range(len(pg.chaves)):
                    saida.append((pg.chaves[k], pg.reservas[k]))
                pilha.pop()
                continue
            if j > len(pg.chaves):
                pilha.pop()
                continue
            if j > 0:
                saida.append((pg.chaves[j - 1], pg.reservas[j - 1]))
            quadro[1] = j + 1
            pilha.append([pg.filhos[j], 0])
        return saida

    def coerente(self):
        t = self.t
        total_chaves = 0
        total_pgs = 0
        nivel_folha = None
        pilha = [(self.raiz, None, None, 1)]
        while pilha:
            pg, lo, hi, nivel = pilha.pop()
            total_pgs += 1
            k = len(pg.chaves)
            total_chaves += k
            if k > 2 * t - 1:
                return False
            if pg is not self.raiz and k < t - 1:
                return False
            if len(pg.reservas) != k:
                return False
            for j in range(k):
                if len(pg.reservas[j]) == 0:
                    return False
                if j > 0 and not pg.chaves[j - 1] < pg.chaves[j]:
                    return False
                if lo is not None and not pg.chaves[j] > lo:
                    return False
                if hi is not None and not pg.chaves[j] < hi:
                    return False
            if pg.folha:
                if pg.filhos:
                    return False
                if nivel_folha is None:
                    nivel_folha = nivel
                elif nivel_folha != nivel:
                    return False
            else:
                if len(pg.filhos) != k + 1:
                    return False
                for j in range(k + 1):
                    clo = pg.chaves[j - 1] if j > 0 else lo
                    chi = pg.chaves[j] if j < k else hi
                    pilha.append((pg.filhos[j], clo, chi, nivel + 1))
        return total_chaves == self.n_chaves and total_pgs == self.n_paginas


if __name__ == "__main__":
    import random
    random.seed(11)
    falhas = 0
    for t in (2, 3, 5):
        for n in (0, 1, 2, 10, 100, 500):
            dados = [random.randint(0, 3 * n + 5) for _ in range(n)]   
            ab = ArvoreB(t)
            for i, x in enumerate(dados):
                ab.inserir(x, i)
                if not ab.coerente():
                    falhas += 1
                    break
            esperado = {}
            for i, x in enumerate(dados):
                esperado.setdefault(x, []).append(i)
            ok_ordem = [(c, r) for c, r in ab.em_ordem()] == [(c, esperado[c]) for c in sorted(esperado)]
            ok_busca = all(ab.buscar(c)[0] == esperado[c] for c in esperado) and ab.buscar(-1)[0] == []
            lo, hi = n // 3, n
            ok_faixa = True
            if n:
                got, _ = ab.faixa(lo, hi)
                ok_faixa = got == [i for c in sorted(esperado) if lo <= c <= hi for i in esperado[c]]
            print("t=%d n=%3d  coerente=%s ordem=%s busca=%s faixa=%s altura=%d paginas=%d" % (
                t, n, ab.coerente(), ok_ordem, ok_busca, ok_faixa, ab.altura(), ab.n_paginas))
            falhas += (not ab.coerente()) + (not ok_ordem) + (not ok_busca) + (not ok_faixa)
    print("FALHAS:", falhas)
