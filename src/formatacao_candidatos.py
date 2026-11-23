"""Formatação de nomes de candidatos para apresentação em cédulas."""

from collections import Counter

_PARTICULAS_SOBRENOME = {"da", "das", "de", "do", "dos", "e"}


def formatar_nomes_candidatos(
    candidatos: list[str], partidos_candidatos: dict[str, list[str]]
) -> dict[str, str]:
    """Retorna rótulos ``SOBRENOME, Nome, Partido`` sem alterar os IDs.

    O último sobrenome pode conter partículas comuns em nomes em português.
    O nome do meio é incluído quando dois candidatos do mesmo partido têm o
    mesmo sobrenome e primeiro nome, para que os rótulos continuem distintos.
    """
    partido_por_candidato = {
        candidato: partido
        for partido, membros in partidos_candidatos.items()
        for candidato in membros
    }
    componentes: dict[str, tuple[str, list[str], str]] = {}

    for candidato in candidatos:
        partes = candidato.split()
        if len(partes) < 2:
            componentes[candidato] = ("", partes, partido_por_candidato.get(candidato, ""))
            continue

        inicio_sobrenome = len(partes) - 1
        while (
            inicio_sobrenome > 1
            and partes[inicio_sobrenome - 1].casefold() in _PARTICULAS_SOBRENOME
        ):
            inicio_sobrenome -= 1

        sobrenome = " ".join(partes[inicio_sobrenome:]).upper()
        nomes = partes[:inicio_sobrenome]
        componentes[candidato] = (
            sobrenome,
            nomes,
            partido_por_candidato.get(candidato, ""),
        )

    chaves_basicas = [
        (sobrenome, nomes[0] if nomes else "", partido.casefold())
        for sobrenome, nomes, partido in componentes.values()
    ]
    frequencias = Counter(chaves_basicas)

    rotulos: dict[str, str] = {}
    for candidato, (sobrenome, nomes, partido) in componentes.items():
        nome_exibido = " ".join(nomes)
        chave_basica = (sobrenome, nomes[0] if nomes else "", partido.casefold())
        if len(nomes) > 1 and frequencias[chave_basica] > 1:
            # Acrescenta os nomes do meio quando o formato curto não distingue
            # candidatos do mesmo partido.
            nome_exibido = " ".join(nomes)
        elif nomes:
            nome_exibido = nomes[0]

        partes_rotulo = [parte for parte in (sobrenome, nome_exibido, partido) if parte]
        rotulos[candidato] = ", ".join(partes_rotulo)

    return rotulos
