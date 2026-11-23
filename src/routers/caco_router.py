import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.autenticacao.base import Usuario
from src.caco import EleicaoAssembleia, OpcaoVoto
from src.database import carregar_estado_sql, salvar_estado_sql

from .dependencias import obter_usuario_logado

# Pega o diretório absoluto onde o main.py está (a pasta src/)
BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(prefix="/caco", tags=["CACo"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Mutex global para impedir condições de corrida quando 2 membros da gestão clicam ao mesmo tempo
_CACO_PAUTA_LOCK = threading.Lock()
_TZ_BRASIL = timezone(timedelta(hours=-3))

def _validar_data_hora_assembleia(data_str: str, hora_str: str) -> datetime:
    """Valida formato, existência real da data/hora (ex: rejeita 31/02 ou 25:00) e bloqueia passado."""
    try:
        dt_agendada = datetime.strptime(
            f"{data_str.strip()} {hora_str.strip()}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=_TZ_BRASIL)
    except ValueError as exc:
        raise ValueError("Data ou horário inexistente/inválido. Use data válida (AAAA-MM-DD) e hora (HH:MM).") from exc

    if dt_agendada < datetime.now(_TZ_BRASIL):
        raise ValueError("Não é permitido agendar uma assembleia em uma data ou horário no passado.")
    return dt_agendada

def _obter_assembleias_caco(app_state) -> dict:
    """Gerencia o dicionário de múltiplas assembleias, sincronizando a 'principal' com app_state.eleicao_caco."""
    if not hasattr(app_state, "assembleias_caco"):
        app_state.assembleias_caco = carregar_estado_sql("assembleias_caco") or {}
    if not hasattr(app_state, "eleitores_caco_votaram"):
        app_state.eleitores_caco_votaram = set()

    eleicao_legada: EleicaoAssembleia = app_state.eleicao_caco
    if "principal" not in app_state.assembleias_caco:
        app_state.assembleias_caco["principal"] = {
            "id": "principal",
            "titulo": "Assembleia Geral Ordinária — CACo",
            "descricao": "Deliberação estudantil geral do Centro Acadêmico da Computação.",
            "local": "Auditório do IC-3 / Unicamp",
            "data": datetime.now(_TZ_BRASIL).strftime("%Y-%m-%d"),
            "horario": datetime.now(_TZ_BRASIL).strftime("%H:%M"),
            "encerrada": False,
            "pautas": [
                {
                    "id": "pauta_principal",
                    "titulo": "Pauta Geral da Assembleia",
                    "descricao": "Votação ordinária da ordem do dia.",
                    "motor": eleicao_legada,
                    "votantes": app_state.eleitores_caco_votaram,
                    "ja_iniciada": eleicao_legada.estado.nome != "AGUARDANDO",
                    "fila_falas": [],
                    "orador_atual": None,
                    "historico_falas": [],
                }
            ],
        }
    else:
        app_state.assembleias_caco["principal"]["pautas"][0]["motor"] = eleicao_legada
        app_state.assembleias_caco["principal"]["pautas"][0]["votantes"] = app_state.eleitores_caco_votaram

    return app_state.assembleias_caco

def _sincronizar_participante_caco(motor: EleicaoAssembleia, usuario: Usuario) -> None:
    """Garante que o usuário autenticado no escopo CACo conste como aluno e eleitor elegível."""
    if "CACO" in usuario.escopo:
        motor.alunos_cadastrados.add(usuario.id)
        motor.eleitores.add(usuario.id)

@router.post("/iniciar")
async def iniciar_votacao_caco(
    request: Request, 
    usuario: Annotated [Usuario, Depends(obter_usuario_logado)]
):
    if "CACO_GESTAO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    eleicao = request.app.state.eleicao_caco

    try:
        eleicao.iniciar_votacao()
        salvar_estado_sql("eleicao_caco", request.app.state.eleicao_caco)
        salvar_estado_sql("eleitores_caco_votaram", request.app.state.eleitores_caco_votaram)
        
        return templates.TemplateResponse(
            request=request,
            name="sucesso.html",
            context={"mensagem": "Votação da Assembleia iniciada com sucesso!"}
        )
    except RuntimeError as e:
        return templates.TemplateResponse(
            request=request,
            name="caco.html",
            context={
                "erro": str(e),
                "estado_eleicao": eleicao.estado.nome,
                "is_gestao": True
            }
        )

@router.get("/assembleia", response_class=HTMLResponse)
async def tela_assembleia(
    request: Request, 
    usuario: Annotated [Usuario, Depends(obter_usuario_logado)]
):
    if "CACO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)
        
    eleicao = request.app.state.eleicao_caco
    _sincronizar_participante_caco(eleicao, usuario)

    is_gestao = "GESTAO" in usuario.escopo
    ja_votou = usuario.id in getattr(eleicao, "votantes", set())
        
    return templates.TemplateResponse(
        name="caco.html", 
        request=request,
        context={
            "estado_eleicao": eleicao.estado.nome,
            "is_gestao": is_gestao,
            "ja_votou" : ja_votou,
        },
    )
    
@router.post("/votar")
async def processar_voto_caco(
    request: Request, 
    usuario: Annotated [Usuario, Depends(obter_usuario_logado)], opcao: str = Form(...)
):
    if "CACO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    # Puxa o contexto global de eleição
    eleicao = request.app.state.eleicao_caco
    _sincronizar_participante_caco(eleicao, usuario)
    is_gestao = "GESTAO" in usuario.escopo

    # Bloqueia se o usuário já votou
    if usuario.id in request.app.state.eleitores_caco_votaram:
        return templates.TemplateResponse(
            request=request,
            name="caco.html",
            context={
                "erro": "VOTO NEGADO: Você já registrou seu voto nesta pauta.",
                "estado_eleicao": eleicao.estado.nome,
                "is_gestao": is_gestao
            }
        )

    try:
        opcao_enum = OpcaoVoto[opcao]
        
        eleicao.apurar_voto(usuario.id, opcao_enum)
        
        # Assina a lista de presença marcando que o ID já votou
        request.app.state.eleitores_caco_votaram.add(usuario.id)
        salvar_estado_sql("eleicao_caco", request.app.state.eleicao_caco)
        salvar_estado_sql("eleitores_caco_votaram", request.app.state.eleitores_caco_votaram)
        return templates.TemplateResponse(
            request=request, 
            name="sucesso.html", 
            context={"mensagem": f"Seu voto na assembleia foi contabilizado como: {opcao}"}
        )
    except (RuntimeError, KeyError, ValueError) as e:
        return templates.TemplateResponse(
            request=request,
            name="caco.html",
            context={
                "erro": str(e),
                "estado_eleicao": eleicao.estado.nome,
                "is_gestao": is_gestao
            }
        )

@router.post("/encerrar")
async def encerrar_votacao_caco(request: Request, usuario: Annotated [Usuario, Depends(obter_usuario_logado)]):
    if "CACO_GESTAO" not in usuario.escopo:
        return RedirectResponse(url="/", status_code=302)

    eleicao = request.app.state.eleicao_caco

    try:
        # Garante que a votação será fechada
        eleicao.encerrar_votacao()
        salvar_estado_sql("eleicao_caco", request.app.state.eleicao_caco)
        salvar_estado_sql("eleitores_caco_votaram", request.app.state.eleitores_caco_votaram)
        return templates.TemplateResponse(
            request=request,
            name="sucesso.html",
            context={"mensagem": "Votação da Assembleia encerrada."}
        )
    except RuntimeError as e:
        return templates.TemplateResponse(
            request=request,
            name="caco.html",
            context={
                "erro": str(e),
                "estado_eleicao": eleicao.estado.nome,
                "is_gestao": True
            }
        )

@router.get("/resultados", response_class=HTMLResponse)
async def resultados_caco(
    request: Request, 
    usuario: Annotated [Usuario, 
    Depends(obter_usuario_logado)]
):
    if "CACO_GESTAO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Acesso negado.")  
    eleicao = request.app.state.eleicao_caco
    contadores = eleicao.obter_contadores()
    # Calcula o total para fazer as barras de porcentagem no HTML
    total_votos = sum(contadores.values())
    
    return templates.TemplateResponse(
        name="resultados_caco.html",
        request=request, 
        context={
            "contadores": contadores,
            "total_votos": total_votos,
            "estado_votacao": eleicao.estado.nome,
        },
    )

def _serializar_contadores(motor: EleicaoAssembleia) -> dict[str, int]:
    """Converte as chaves de obter_contadores() (OpcaoVoto ou str) para dict JSON seguro."""
    return {getattr(k, "name", str(k)): int(v) for k, v in motor.obter_contadores().items()}

@router.get("/api/estado")
async def estado_caco_json(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    assembleia_id: str = "principal",
):
    if "CACO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Acesso restrito ao escopo CACo.")

    assembleias = _obter_assembleias_caco(request.app.state)
    if assembleia_id not in assembleias:
        assembleia_id = next(iter(assembleias.keys()))

    asm = assembleias[assembleia_id]
    pautas_serializadas = []
    pauta_ativa_id = None

    for p in asm["pautas"]:
        motor: EleicaoAssembleia = p["motor"]
        _sincronizar_participante_caco(motor, usuario)
        estado_nome = motor.estado.nome
        if estado_nome == "VOTACAO":
            pauta_ativa_id = p["id"]

        contadores = _serializar_contadores(motor)
        res_vencedor = motor.apurar_vencedor() if estado_nome == "ENCERRADO" else None

        pautas_serializadas.append({
            "id": p["id"],
            "titulo": p["titulo"],
            "descricao": p["descricao"],
            "estado": estado_nome,
            "ja_iniciada": p.get("ja_iniciada", estado_nome != "AGUARDANDO"),
            "ja_votou": usuario.id in p["votantes"],
            "contadores": contadores,
            "total_votos": sum(contadores.values()),
            "resultado": getattr(res_vencedor, "name", str(res_vencedor)) if res_vencedor is not None else None,
            "fila_falas": list(p["fila_falas"]),
            "orador_atual": p["orador_atual"],
            "historico_falas": list(p["historico_falas"]),
        })

    salvar_estado_sql("assembleias_caco", assembleias)
    return JSONResponse({
        "is_gestao": "CACO_GESTAO" in usuario.escopo,
        "assembleia_atual": {
            "id": asm["id"],
            "titulo": asm["titulo"],
            "descricao": asm["descricao"],
            "local": asm["local"],
            "data": asm["data"],
            "horario": asm["horario"],
            "encerrada": asm["encerrada"],
        },
        "assembleias_disponiveis": [
            {
                "id": a["id"],
                "titulo": a["titulo"],
                "data": a["data"],
                "horario": a["horario"],
                "local": a["local"],
                "encerrada": a["encerrada"],
                "total_pautas": len(a["pautas"]),
            }
            for a in assembleias.values()
        ],
        "pauta_ativa_id": pauta_ativa_id,
        "pautas": pautas_serializadas,
    })


@router.post("/api/assembleias")
async def criar_nova_assembleia(
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    titulo: str = Form(...),
    descricao: str = Form(...),
    local: str = Form(...),
    data: str = Form(...),
    horario: str = Form(...),
):
    if "CACO_GESTAO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas a Gestão do CACo pode criar assembleias.")

    if not titulo.strip() or not descricao.strip() or not local.strip():
        raise HTTPException(status_code=400, detail="Título, descrição e local são obrigatórios.")

    try:
        _validar_data_hora_assembleia(data, horario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    assembleias = _obter_assembleias_caco(request.app.state)
    novo_id = f"asm_{int(time.time() * 1000)}"
    assembleias[novo_id] = {
        "id": novo_id,
        "titulo": titulo.strip(),
        "descricao": descricao.strip(),
        "local": local.strip(),
        "data": data.strip(),
        "horario": horario.strip(),
        "encerrada": False,
        "pautas": [],
    }
    salvar_estado_sql("assembleias_caco", assembleias)
    return JSONResponse({"status": "criada", "assembleia_id": novo_id})


@router.post("/api/assembleias/{assembleia_id}/encerrar")
async def encerrar_assembleia_completa(
    assembleia_id: str,
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
):
    if "CACO_GESTAO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas a Gestão do CACo pode encerrar assembleias.")

    assembleias = _obter_assembleias_caco(request.app.state)
    if assembleia_id not in assembleias:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada.")

    asm = assembleias[assembleia_id]
    with _CACO_PAUTA_LOCK:
        for p in asm["pautas"]:
            if p["motor"].estado.nome == "VOTACAO":
                p["motor"].encerrar_votacao()
        asm["encerrada"] = True

    salvar_estado_sql("assembleias_caco", assembleias)
    return JSONResponse({"status": "encerrada"})


@router.post("/api/assembleias/{assembleia_id}/pautas")
async def criar_pauta_na_assembleia(
    assembleia_id: str,
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    titulo: str = Form(...),
    descricao: str = Form(...),
):
    if "CACO_GESTAO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas a Gestão do CACo pode criar pautas.")

    assembleias = _obter_assembleias_caco(request.app.state)
    asm = assembleias.get(assembleia_id)
    if not asm:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada.")

    if asm["encerrada"]:
        raise HTTPException(status_code=400, detail="Não é possível adicionar pautas a uma assembleia encerrada.")

    if not titulo.strip() or not descricao.strip():
        raise HTTPException(status_code=400, detail="Título e descrição da pauta são obrigatórios.")

    ids_base = list(request.app.state.eleicao_caco.alunos_cadastrados | {usuario.id})
    novo_motor = EleicaoAssembleia(alunos_cadastrados=ids_base, eleitores=ids_base, duracao=60)
    nova_pauta = {
        "id": f"pauta_{int(time.time() * 1000)}_{len(asm['pautas'])}",
        "titulo": titulo.strip(),
        "descricao": descricao.strip(),
        "motor": novo_motor,
        "votantes": set(),
        "ja_iniciada": False,
        "fila_falas": [],
        "orador_atual": None,
        "historico_falas": [],
    }
    asm["pautas"].append(nova_pauta)
    salvar_estado_sql("assembleias_caco", assembleias)
    return JSONResponse({"status": "criada", "pauta_id": nova_pauta["id"]})


@router.post("/api/assembleias/{assembleia_id}/pautas/{pauta_id}/iniciar")
async def iniciar_pauta_concorrente(
    assembleia_id: str,
    pauta_id: str,
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
):
    """Inicia uma pauta com trava de concorrência: apenas 1 pauta ativa por assembleia e sem reabertura."""
    if "CACO_GESTAO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas a Gestão do CACo pode iniciar pautas.")

    assembleias = _obter_assembleias_caco(request.app.state)
    asm = assembleias.get(assembleia_id)
    if not asm:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada.")

    if asm["encerrada"]:
        raise HTTPException(status_code=400, detail="Esta assembleia já foi encerrada.")

    with _CACO_PAUTA_LOCK:
        # 1. Garante exclusão mútua: nenhuma outra pauta pode estar em votação no momento
        for outra in asm["pautas"]:
            if outra["motor"].estado.nome == "VOTACAO":
                raise HTTPException(
                    status_code=409,
                    detail=f"Já existe uma pauta em votação ('{outra['titulo']}'). Encerre-a antes de iniciar outra!",
                )

        alvo = next((p for p in asm["pautas"] if p["id"] == pauta_id), None)
        if not alvo:
            raise HTTPException(status_code=404, detail="Pauta não encontrada.")

        # 2. Impede reabrir pauta já encerrada ou já iniciada anteriormente
        if alvo["motor"].estado.nome == "ENCERRADO" or alvo.get("ja_iniciada", False):
            raise HTTPException(
                status_code=400,
                detail="Esta pauta já foi votada e encerrada! Crie uma nova pauta se precisar deliberar novamente.",
            )

        _sincronizar_participante_caco(alvo["motor"], usuario)
        try:
            alvo["motor"].iniciar_votacao()
            alvo["ja_iniciada"] = True
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    salvar_estado_sql("assembleias_caco", assembleias)
    return JSONResponse({"status": "iniciada", "pauta_id": pauta_id})


@router.post("/api/assembleias/{assembleia_id}/pautas/{pauta_id}/encerrar")
async def encerrar_pauta_especifica(
    assembleia_id: str,
    pauta_id: str,
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
):
    if "CACO_GESTAO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas a Gestão do CACo pode encerrar pautas.")

    assembleias = _obter_assembleias_caco(request.app.state)
    asm = assembleias.get(assembleia_id)
    if not asm:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada.")

    with _CACO_PAUTA_LOCK:
        alvo = next((p for p in asm["pautas"] if p["id"] == pauta_id), None)
        if not alvo:
            raise HTTPException(status_code=404, detail="Pauta não encontrada.")
        if alvo["motor"].estado.nome != "VOTACAO":
            raise HTTPException(status_code=400, detail="Apenas pautas em votação podem ser encerradas.")
        alvo["motor"].encerrar_votacao()

    res = alvo["motor"].apurar_vencedor()
    salvar_estado_sql("assembleias_caco", assembleias)
    return JSONResponse({"status": "encerrada", "resultado": getattr(res, "name", str(res)) if res else None})

@router.post("/api/assembleias/{assembleia_id}/pautas/{pauta_id}/votar")
async def votar_na_pauta_caco(
    assembleia_id: str,
    pauta_id: str,
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    opcao: str = Form(...),
):
    if "CACO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas membros do CACo podem votar.")

    assembleias = _obter_assembleias_caco(request.app.state)
    asm = assembleias.get(assembleia_id)
    if not asm:
        raise HTTPException(status_code=404, detail="Assembleia não encontrada.")
    if asm["encerrada"]:
        raise HTTPException(status_code=400, detail="Esta assembleia já está encerrada.")

    alvo = next((p for p in asm["pautas"] if p["id"] == pauta_id), None)
    if not alvo:
        raise HTTPException(status_code=404, detail="Pauta não encontrada.")
    if usuario.id in alvo["votantes"]:
        raise HTTPException(status_code=400, detail="VOTO NEGADO: Você já registrou seu voto nesta pauta.")

    motor: EleicaoAssembleia = alvo["motor"]
    _sincronizar_participante_caco(motor, usuario)
    try:
        opcao_enum = OpcaoVoto[opcao]
        motor.apurar_voto(usuario.id, opcao_enum)
        alvo["votantes"].add(usuario.id)
    except (RuntimeError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
        
    salvar_estado_sql("assembleias_caco", assembleias)
    return JSONResponse({"status": "ok", "mensagem": f"Voto '{opcao}' registrado na pauta '{alvo['titulo']}'!"})

@router.post("/api/assembleias/{assembleia_id}/pautas/{pauta_id}/falas/inscrever")
async def inscrever_fala_pauta(
    assembleia_id: str,
    pauta_id: str,
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
    tipo_fala: str = Form("Fala Ordinária"),
):
    if "CACO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas membros do CACo podem pedir fala.")

    assembleias = _obter_assembleias_caco(request.app.state)
    asm = assembleias.get(assembleia_id)
    if not asm or asm["encerrada"]:
        raise HTTPException(status_code=400, detail="Assembleia indisponível ou encerrada.")

    alvo = next((p for p in asm["pautas"] if p["id"] == pauta_id), None)
    if not alvo:
        raise HTTPException(status_code=404, detail="Pauta não encontrada.")
    if alvo["motor"].estado.nome == "ENCERRADO":
        raise HTTPException(status_code=400, detail="Não é possível se inscrever para falar em pauta já encerrada.")

    if any(f["user_id"] == usuario.id for f in alvo["fila_falas"]):
        raise HTTPException(status_code=400, detail="Você já está inscrito na fila de falas desta pauta.")

    alvo["fila_falas"].append({
        "user_id": usuario.id,
        "username": usuario.username,
        "nome": usuario.nome_real,
        "tipo": tipo_fala.strip() or "Fala Ordinária",
        "inscrito_em": datetime.now(_TZ_BRASIL).strftime("%H:%M:%S"),
    })
    salvar_estado_sql("assembleias_caco", assembleias)
    return JSONResponse({"status": "inscrito"})


@router.post("/api/assembleias/{assembleia_id}/pautas/{pauta_id}/falas/proximo")
async def chamar_proximo_orador(
    assembleia_id: str,
    pauta_id: str,
    request: Request,
    usuario: Annotated[Usuario, Depends(obter_usuario_logado)],
):
    if "CACO_GESTAO" not in usuario.escopo:
        raise HTTPException(status_code=403, detail="Apenas a Gestão pode conduzir a fila de falas.")

    assembleias = _obter_assembleias_caco(request.app.state)
    asm = assembleias.get(assembleia_id)
    alvo = next((p for p in asm["pautas"] if p["id"] == pauta_id), None) if asm else None
    if not alvo:
        raise HTTPException(status_code=404, detail="Pauta não encontrada.")

    if alvo["orador_atual"]:
        alvo["historico_falas"].append({
            **alvo["orador_atual"],
            "resumo": "Fala concluída.",
        })
        alvo["orador_atual"] = None

    if alvo["fila_falas"]:
        proximo = alvo["fila_falas"].pop(0)
        proximo["inicio_fala"] = datetime.now(_TZ_BRASIL).strftime("%H:%M:%S")
        alvo["orador_atual"] = proximo

    salvar_estado_sql("assembleias_caco", assembleias)
    return JSONResponse({"status": "ok", "orador_atual": alvo["orador_atual"]})