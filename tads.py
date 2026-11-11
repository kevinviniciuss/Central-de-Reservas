class _No:
    __slots__ = ("valor", "prox")

    def __init__(self, valor):
        self.valor = valor
        self.prox = None


class Fila:
    def __init__(self):
        self._inicio = None   
        self._fim = None      
        self._tamanho = 0
        self.operacoes = 0

    def enfileirar(self, valor):
        no = _No(valor)
        if self._fim is None:
            self._inicio = no
        else:
            self._fim.prox = no
        self._fim = no
        self._tamanho += 1
        self.operacoes += 1

    def desenfileirar(self):
        if self._inicio is None:
            raise IndexError("fila vazia")
        no = self._inicio
        self._inicio = no.prox
        if self._inicio is None:
            self._fim = None
        self._tamanho -= 1
        self.operacoes += 1
        return no.valor

    def frente(self):
        if self._inicio is None:
            raise IndexError("fila vazia")
        return self._inicio.valor

    def vazia(self):
        return self._tamanho == 0

    def tamanho(self):
        return self._tamanho


class Pilha:
    def __init__(self):
        self._topo = None
        self._tamanho = 0
        self.operacoes = 0

    def empilhar(self, valor):
        no = _No(valor)
        no.prox = self._topo
        self._topo = no
        self._tamanho += 1
        self.operacoes += 1

    def desempilhar(self):
        if self._topo is None:
            raise IndexError("pilha vazia")
        no = self._topo
        self._topo = no.prox
        self._tamanho -= 1
        self.operacoes += 1
        return no.valor

    def espiar(self):
        if self._topo is None:
            raise IndexError("pilha vazia")
        return self._topo.valor

    def vazia(self):
        return self._tamanho == 0

    def tamanho(self):
        return self._tamanho
