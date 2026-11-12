
import json
import os
import csv
import visual as v

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(PASTA, "inventario.json")


def carregar_recursos():
    if not os.path.exists(ARQUIVO):
        return []

    with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    return dados.get("recursos", [])


def salvar_recursos(recursos):
    dados = {"recursos": recursos}

    with open(ARQUIVO, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)


def validar_recurso(recurso):
    campos = ("codigo", "nome", "tipo", "local")

    for campo in campos:
        if not str(recurso.get(campo, "")).strip():
            raise ValueError("O campo '%s' é obrigatório." % campo)

    if not isinstance(recurso.get("quantidade", 1), int):
        raise ValueError("A quantidade deve ser um número inteiro.")

    if recurso.get("quantidade", 1) < 0:
        raise ValueError("A quantidade não pode ser negativa.")

    return True


def validar_reserva(reserva):
    campos = ("recurso", "inicio", "fim")

    for campo in campos:
        if campo not in reserva or reserva[campo] is None:
            raise ValueError("Campo obrigatório ausente: %s" % campo)

    if not isinstance(reserva["inicio"], int):
        raise ValueError("O início deve estar em minutos.")

    if not isinstance(reserva["fim"], int):
        raise ValueError("O fim deve estar em minutos.")

    if reserva["fim"] <= reserva["inicio"]:
        raise ValueError("O fim precisa ser posterior ao início.")

    return True


def tela(titulo):
    v.cabecalho(titulo, "ProTec")


def cadastrar_recurso():
    tela("Cadastrar recurso")
    recursos = carregar_recursos()

    try:
        recurso = {
            "codigo": v.ler("Código"),
            "nome": v.ler("Nome"),
            "tipo": v.ler("Tipo"),
            "local": v.ler("Local"),
            "quantidade": int(v.ler("Quantidade")),
            "marca": "",
            "modelo": "",
            "estado": "Pendente de vistoria",
            "disponibilidade": "Não verificada",
            "observacoes": ""
        }

        validar_recurso(recurso)

        for existente in recursos:
            if existente["codigo"].lower() == recurso["codigo"].lower():
                raise ValueError("Já existe um recurso com esse código.")

        recursos.append(recurso)
        salvar_recursos(recursos)

        v.ok("Recurso cadastrado com sucesso!")

    except ValueError as erro:
        v.erro(str(erro))


def listar_recursos():
    tela("Inventário de recursos")
    recursos = carregar_recursos()

    if not recursos:
        v.aviso("Nenhum recurso cadastrado.")
        return

    v.resumo([
        ("Total de cadastros", len(recursos))
    ])

    for recurso in recursos:
        print()
        v.secao(recurso["nome"])

        print(
            v.c("Código: ", "muted") +
            v.c(recurso["codigo"], "bold", "ouro")
        )
        print(v.c("Tipo: ", "muted") + recurso["tipo"])
        print(v.c("Local: ", "muted") + recurso["local"])
        print(v.c("Quantidade: ", "muted") + str(recurso["quantidade"]))
        print(v.c("Estado: ", "muted") + recurso["estado"])


def editar_recurso():
    tela("Editar recurso")
    recursos = carregar_recursos()

    codigo = v.ler("Código do recurso")

    for recurso in recursos:
        if recurso["codigo"].lower() == codigo.lower():

            v.info("Deixe vazio para manter o valor atual.")

            for campo in ("nome", "tipo", "local"):
                novo = v.ler(
                    "%s (%s)" % (campo.capitalize(), recurso[campo])
                )

                if novo:
                    recurso[campo] = novo

            quantidade = v.ler(
                "Quantidade (%s)" % recurso["quantidade"]
            )

            if quantidade:
                try:
                    recurso["quantidade"] = int(quantidade)
                except ValueError:
                    v.erro("A quantidade precisa ser um número inteiro.")
                    return

            try:
                validar_recurso(recurso)
                salvar_recursos(recursos)
                v.ok("Recurso atualizado com sucesso!")

            except ValueError as erro:
                v.erro(str(erro))

            return

    v.erro("Recurso não encontrado.")


def remover_recurso():
    tela("Remover recurso")
    recursos = carregar_recursos()

    codigo = v.ler("Código do recurso")

    novos = [
        recurso for recurso in recursos
        if recurso["codigo"].lower() != codigo.lower()
    ]

    if len(novos) == len(recursos):
        v.erro("Recurso não encontrado.")
        return

    confirmar = v.ler("Confirma a remoção? (S/N)").upper()

    if confirmar != "S":
        v.aviso("Remoção cancelada.")
        return

    salvar_recursos(novos)
    v.ok("Recurso removido com sucesso!")


def importar_ficha_campo(caminho):
    tela("Importar ficha de campo")
    recursos = carregar_recursos()

    try:
        with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
            leitor = csv.DictReader(arquivo, delimiter=";")

            for linha in leitor:
                recurso = {
                    "codigo": linha.get("codigo", "").strip(),
                    "nome": linha.get("nome", "").strip(),
                    "tipo": linha.get("tipo", "").strip(),
                    "local": linha.get("local", "").strip(),
                    "quantidade": int(linha.get("quantidade") or 0),
                    "marca": linha.get("marca", "").strip(),
                    "modelo": linha.get("modelo", "").strip(),
                    "estado": linha.get("estado", "Pendente de vistoria"),
                    "disponibilidade": "Não verificada",
                    "observacoes": linha.get("observacoes", "").strip()
                }

                validar_recurso(recurso)

                existe = any(
                    r["codigo"].lower() == recurso["codigo"].lower()
                    for r in recursos
                )

                if not existe:
                    recursos.append(recurso)

        salvar_recursos(recursos)
        v.ok("Importação concluída!")

    except (OSError, ValueError, csv.Error) as erro:
        v.erro("Falha na importação: " + str(erro))


def menu():
    while True:
        tela("Cadastro de recursos")

        print("  " + v.c("1", "bold", "ouro") + "  Cadastrar recurso")
        print("  " + v.c("2", "bold", "ouro") + "  Listar recursos")
        print("  " + v.c("3", "bold", "ouro") + "  Editar recurso")
        print("  " + v.c("4", "bold", "ouro") + "  Remover recurso")
        print("  " + v.c("5", "bold", "ouro") + "  Importar ficha de campo")
        print("  " + v.c("0", "bold", "ouro") + "  Voltar ao menu principal")
        print()

        opcao = v.ler("Opção")

        if opcao == "1":
            cadastrar_recurso()
            v.pausa()

        elif opcao == "2":
            listar_recursos()
            v.pausa()

        elif opcao == "3":
            editar_recurso()
            v.pausa()

        elif opcao == "4":
            remover_recurso()
            v.pausa()

        elif opcao == "5":
            caminho = v.ler("Caminho do arquivo CSV")
            if caminho:
                importar_ficha_campo(caminho)
            v.pausa()

        elif opcao == "0":
            return

        else:
            v.erro("Opção inválida. Escolha de 0 a 5.")
            v.pausa()
