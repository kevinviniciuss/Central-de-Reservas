from tads import Fila, Pilha


class No:
    __slots__ = ("chave", "reservas", "esq", "dir", "h", "hc")

    def __init__(self, chave, reserva):
        self.chave = chave
        self.reservas = [reserva]
        self.esq = None
        self.dir = None
        self.h = 1   
        self.hc = 0  


def _h(no):
    return no.h if no is not None else 0


def _atualizar(no):
    he, hd = _h(no.esq), _h(no.dir)
    no.h = 1 + (he if he > hd else hd)


class Arvore:
    def __init__(self, balanceada=False):
        self.balanceada = balanceada
        self.raiz = None
        self.n_nos = 0            
        self.n_reservas = 0       
        self.comparacoes = 0      
        self.rotacoes = 0
        self.operacoes_percurso = 0  

    def inserir(self, chave, reserva):
        self.n_reservas += 1
        self.raiz = self._inserir(self.raiz, chave, reserva)

    def _inserir(self, no, chave, reserva):
        if no is None:
            self.n_nos += 1
            return No(chave, reserva)
        self.comparacoes += 1
        if chave == no.chave:
            no.reservas.append(reserva)
            return no
        if chave < no.chave:
            no.esq = self._inserir(no.esq, chave, reserva)
        else:
            no.dir = self._inserir(no.dir, chave, reserva)
        _atualizar(no)
        if self.balanceada:
            return self._rebalancear(no)
        return no

    def _fator(self, no):
        return _h(no.esq) - _h(no.dir)

    def _rebalancear(self, no):
        fb = self._fator(no)
        if fb > 1:                              
            if self._fator(no.esq) < 0:         
                no.esq = self._rot_esquerda(no.esq)
            return self._rot_direita(no)
        if fb < -1:                             
            if self._fator(no.dir) > 0:         
                no.dir = self._rot_direita(no.dir)
            return self._rot_esquerda(no)
        return no

    def _rot_direita(self, y):
        x = y.esq
        y.esq = x.dir
        x.dir = y
        _atualizar(y)
        _atualizar(x)
        self.rotacoes += 1
        return x

    def _rot_esquerda(self, x):
        y = x.dir
        x.dir = y.esq
        y.esq = x
        _atualizar(x)
        _atualizar(y)
        self.rotacoes += 1
        return y

    def buscar(self, chave):
        atual = self.raiz
        comps = 0
        while atual is not None:
            comps += 1
            if chave == atual.chave:
                return atual.reservas, comps
            atual = atual.esq if chave < atual.chave else atual.dir
        return [], comps

    def faixa(self, inicio, fim):
        resultado = []
        visitados = 0
        pilha = Pilha()
        atual = self.raiz
        while True:
            while atual is not None:
                visitados += 1
                if atual.chave < inicio:       
                    atual = atual.dir
                else:
                    pilha.empilhar(atual)
                    atual = atual.esq
            if pilha.vazia():
                break
            no = pilha.desempilhar()
            if no.chave > fim:                 
                break
            resultado.extend(no.reservas)
            atual = no.dir
        return resultado, visitados

    def predecessor(self, chave):
        melhor = None
        atual = self.raiz
        while atual is not None:
            if atual.chave < chave:
                melhor = atual
                atual = atual.dir
            else:
                atual = atual.esq
        return None if melhor is None else (melhor.chave, melhor.reservas)

    def altura(self):
        return _h(self.raiz)

    def caminho_medio(self):
        niveis = self.em_largura_com_fila()
        if self.n_nos == 0:
            return 0.0
        soma = 0
        for i in range(len(niveis)):
            soma += (i + 1) * len(niveis[i])
        return soma / self.n_nos

    def em_ordem_com_pilha(self):
        saida = []
        pilha = Pilha()
        atual = self.raiz
        while atual is not None or not pilha.vazia():
            while atual is not None:
                pilha.empilhar(atual)
                atual = atual.esq
            atual = pilha.desempilhar()
            saida.append((atual.chave, atual.reservas))
            atual = atual.dir
        self.operacoes_percurso = pilha.operacoes
        return saida

    def em_largura_com_fila(self):
        niveis = []
        if self.raiz is None:
            return niveis
        fila = Fila()
        fila.enfileirar(self.raiz)
        while not fila.vazia():
            tam = fila.tamanho()
            nivel = []
            for _ in range(tam):
                no = fila.desenfileirar()
                nivel.append(no.chave)
                if no.esq is not None:
                    fila.enfileirar(no.esq)
                if no.dir is not None:
                    fila.enfileirar(no.dir)
            niveis.append(nivel)
        self.operacoes_percurso = fila.operacoes
        return niveis

    def coerente(self):
        if self.raiz is None:
            return True
        pilha = Pilha()
        pilha.empilhar((self.raiz, None, None))
        ordem = []   
        contados = 0
        while not pilha.vazia():
            no, lo, hi = pilha.desempilhar()
            if (lo is not None and no.chave <= lo) or (hi is not None and no.chave >= hi):
                return False
            if len(no.reservas) == 0:
                return False
            contados += 1
            ordem.append(no)
            if no.esq is not None:
                pilha.empilhar((no.esq, lo, no.chave))
            if no.dir is not None:
                pilha.empilhar((no.dir, no.chave, hi))
        if contados != self.n_nos:
            return False
        for i in range(len(ordem) - 1, -1, -1):
            no = ordem[i]
            he = no.esq.hc if no.esq is not None else 0
            hd = no.dir.hc if no.dir is not None else 0
            no.hc = 1 + (he if he > hd else hd)
            if no.hc != no.h:
                return False
            if self.balanceada and abs(he - hd) > 1:
                return False
        return True
