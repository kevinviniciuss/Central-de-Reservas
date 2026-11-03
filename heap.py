"""heap.py - min-heap em array, heapsort e k menores com heap.

Itens do heap: pares (chave, carga). A chave e comparada com `<` (inteiro ou tupla;
tupla compara campo a campo, o que permite desempate: (prioridade, id)).
O menor ficar na raiz: indice 0. Pai de i = (i-1)//2; filhos = 2i+1 e 2i+2.

Convencoes de contagem (valem para Heap, heapsort e k_menores_com_heap):
  * comparacoes: 1 por comparacao entre duas chaves.
  * trocas: 1 por troca de duas posicoes do array.
Nao usa heapq nem sorted() fora das funcoes de verificacao (final do arquivo).
"""


class Heap:
    def __init__(self):
        self._v = []          # array; so as posicoes 0.._n-1 valem
        self._n = 0
        self.comparacoes = 0
        self.trocas = 0
        self.operacoes = 0    # inserir + remover_topo

    # ---------------------------------------------------------- basicas
    def tamanho(self):
        return self._n

    def vazia(self):
        return self._n == 0

    def topo(self):
        if self._n == 0:
            raise IndexError("heap vazio")
        return self._v[0]

    def _trocar(self, i, j):
        self._v[i], self._v[j] = self._v[j], self._v[i]
        self.trocas += 1

    def _subir(self, i):
        """heapify na subida: o no i sobe enquanto for menor que o pai."""
        v = self._v
        while i > 0:
            pai = (i - 1) // 2
            self.comparacoes += 1
            if v[i][0] < v[pai][0]:
                self._trocar(i, pai)
                i = pai
            else:
                break

    def _descer(self, i):
        """heapify na descida: o no i desce enquanto for maior que algum filho."""
        v = self._v
        n = self._n
        while True:
            esq = 2 * i + 1
            if esq >= n:
                break
            menor = esq
            dir_ = esq + 1
            if dir_ < n:
                self.comparacoes += 1
                if v[dir_][0] < v[esq][0]:
                    menor = dir_
            self.comparacoes += 1
            if v[menor][0] < v[i][0]:
                self._trocar(i, menor)
                i = menor
            else:
                break

    # --------------------------------------------------------- operacoes
    def inserir(self, chave, carga):
        self.operacoes += 1
        item = (chave, carga)
        if self._n < len(self._v):
            self._v[self._n] = item
        else:
            self._v.append(item)
        self._n += 1
        self._subir(self._n - 1)

    def remover_topo(self):
        """Devolve (chave, carga) do menor. Heap vazio -> IndexError."""
        if self._n == 0:
            raise IndexError("heap vazio")
        self.operacoes += 1
        raiz = self._v[0]
        ultimo = self._n - 1
        if ultimo > 0:
            self._trocar(0, ultimo)
        self._v[ultimo] = None
        self._n = ultimo
        if self._n > 1:
            self._descer(0)
        return raiz

    def construir(self, itens):
        """Monta o heap de uma vez (heapify de baixo para cima, O(n)).
        `itens` e uma sequencia de pares (chave, carga)."""
        self._v = [it for it in itens]
        self._n = len(self._v)
        for i in range(self._n // 2 - 1, -1, -1):
            self._descer(i)

    # ---------------------------------------------------------- invariante
    def coerente(self):
        """True se a propriedade de min-heap vale em todo no (pai <= filho) e nao ha
        posicao vazia dentro do tamanho. Nao mexe nos contadores."""
        for i in range(self._n):
            if self._v[i] is None:
                return False
            if i > 0 and self._v[i][0] < self._v[(i - 1) // 2][0]:
                return False
        return True


# ------------------------------------------------------------------ heapsort
def _descer_max(a, i, n, kf, cont):
    """Desce o no i de um MAX-heap em a[0:n]. cont = [comparacoes, trocas]."""
    while True:
        esq = 2 * i + 1
        if esq >= n:
            return
        maior = esq
        dir_ = esq + 1
        if dir_ < n:
            cont[0] += 1
            if kf(a[dir_]) > kf(a[esq]):
                maior = dir_
        cont[0] += 1
        if kf(a[maior]) > kf(a[i]):
            a[i], a[maior] = a[maior], a[i]
            cont[1] += 1
            i = maior
        else:
            return


def heapsort(itens, chave=None):
    """Ordena em ordem crescente. Devolve (lista_ordenada, comparacoes, trocas).
    `chave(item)` extrai a chave de comparacao (padrao: o proprio item).
    Nao altera a lista recebida."""
    kf = chave if chave is not None else (lambda x: x)
    a = [x for x in itens]
    n = len(a)
    cont = [0, 0]
    for i in range(n // 2 - 1, -1, -1):          # monta o max-heap
        _descer_max(a, i, n, kf, cont)
    for fim in range(n - 1, 0, -1):               # leva o maior para o fim
        a[0], a[fim] = a[fim], a[0]
        cont[1] += 1
        _descer_max(a, 0, fim, kf, cont)
    return a, cont[0], cont[1]


def k_menores_com_heap(itens, k, chave=None):
    """Os k menores itens, em ordem, SEM ordenar tudo: monta um min-heap (O(n)) e
    extrai k vezes. Devolve (lista_dos_k, comparacoes, trocas); as contagens
    incluem a montagem do heap."""
    kf = chave if chave is not None else (lambda x: x)
    h = Heap()
    h.construir([(kf(x), x) for x in itens])
    saida = []
    for _ in range(min(k, h.tamanho())):
        saida.append(h.remover_topo()[1])
    return saida, h.comparacoes, h.trocas


# ------------------------------------------------------------- verificacao
# Unico lugar onde a biblioteca padrao (heapq, sorted) aparece: so responde
# True/False, nao produz nenhum numero do relatorio.
def verificar_ordem_de_saida(chaves):
    """Confere, com heapq, se o Heap devolve as chaves na mesma ordem."""
    import heapq
    h = Heap()
    for i, ch in enumerate(chaves):
        h.inserir(ch, i)
    meu = []
    while not h.vazia():
        meu.append(h.remover_topo()[0])
    ref = list(chaves)
    heapq.heapify(ref)
    esperado = [heapq.heappop(ref) for _ in range(len(chaves))]
    return meu == esperado


def verificar_heapsort(itens):
    """Confere heapsort e k_menores_com_heap contra sorted()."""
    ordenado, _, _ = heapsort(itens)
    if ordenado != sorted(itens):
        return False
    for k in (0, 1, 5, len(itens), len(itens) + 3):
        menores, _, _ = k_menores_com_heap(itens, k)
        if menores != sorted(itens)[:k]:
            return False
    return True


if __name__ == "__main__":
    # Autoteste:  python heap.py
    import random
    random.seed(7)
    falhas = 0
    for n in (0, 1, 2, 3, 10, 50, 240):
        dados = [random.randint(0, 40) for _ in range(n)]   # com repeticoes
        h = Heap()
        for i, x in enumerate(dados):
            h.inserir(x, i)
            if not h.coerente():
                falhas += 1
        while not h.vazia():
            h.remover_topo()
            if not h.coerente():
                falhas += 1
        ok1 = verificar_ordem_de_saida(dados)
        ok2 = verificar_heapsort(dados)
        h2 = Heap()
        h2.construir([(x, x) for x in dados])
        ok3 = h2.coerente()
        print("n=%3d  saida=%s  heapsort=%s  construir=%s" % (n, ok1, ok2, ok3))
        falhas += (not ok1) + (not ok2) + (not ok3)
    print("FALHAS:", falhas)
