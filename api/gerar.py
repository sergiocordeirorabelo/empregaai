"""
EmpregaAI v2 — Backend Completo
- Currículo profissional via Claude API
- Vagas reais SOMENTE do Brasil (Emprega Brasil + Indeed Brasil)
- Perfil LinkedIn gerado
- Email de candidatura personalizado
- Dicas de entrevista personalizadas
"""

import json
import os
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

# ─────────────────────────────────────────────
# MAPA CIDADES → IBGE (somente Brasil)
# ─────────────────────────────────────────────
CIDADES_IBGE = {
    "manaus": "1302603", "são paulo": "3550308", "sao paulo": "3550308",
    "rio de janeiro": "3304557", "belo horizonte": "3106200",
    "brasilia": "5300108", "brasília": "5300108", "salvador": "2927408",
    "fortaleza": "2304400", "curitiba": "4106902", "recife": "2611606",
    "porto alegre": "4314902", "belém": "1501402", "belem": "1501402",
    "goiania": "5208707", "goiânia": "5208707", "campinas": "3509502",
    "natal": "2408102", "maceio": "2704302", "maceió": "2704302",
    "joao pessoa": "2507507", "joão pessoa": "2507507", "teresina": "2211001",
    "campo grande": "5002704", "porto velho": "1100205",
    "macapa": "1600303", "macapá": "1600303", "boa vista": "1400100",
    "rio branco": "1200401", "palmas": "1721000",
    "florianopolis": "4205407", "florianópolis": "4205407",
    "vitoria": "3205309", "vitória": "3205309", "aracaju": "2800308",
    "cuiaba": "5103403", "cuiabá": "5103403",
}

# ─────────────────────────────────────────────
# BUSCA VAGAS — SOMENTE BRASIL
# ─────────────────────────────────────────────
def buscar_vagas_brasil(cidade: str, area: str) -> list:
    """
    Busca vagas somente no Brasil.
    1. Tenta API Emprega Brasil (governo federal)
    2. Complementa com links diretos do Indeed Brasil e Gupy
    Filtra qualquer resultado fora do Brasil.
    """
    cidade_limpa = cidade.lower().split(",")[0].strip()
    cod_municipio = CIDADES_IBGE.get(cidade_limpa, "1302603")
    area_limpa = area.split(",")[0].replace("💼","").replace("💻","").replace("📊","").replace("🎨","").replace("🛒","").replace("🤝","").replace("📦","").replace("🏥","").replace("📣","").replace("🔧","").strip()
    cidade_formatada = cidade.split(",")[0].strip()

    vagas = []

    # 1. API Emprega Brasil
    try:
        url = (
            f"https://servicosapigateway.empregabrasil.mte.gov.br/vagas/v1/vagas"
            f"?codigoMunicipio={cod_municipio}&qtdVagas=8&pagina=1"
        )
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "EmpregaAI/2.0"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        items = data.get("vagas", data.get("data", data.get("items", [])))
        for v in items[:5]:
            municipio = v.get("municipio", cidade_formatada)
            # Filtra vagas fora do Brasil
            if any(pais in str(municipio).lower() for pais in ["united", "usa", "eua", "estados unidos"]):
                continue
            vagas.append({
                "cargo":   v.get("nomeCargo", v.get("cargo", f"Vaga de {area_limpa}")),
                "empresa": v.get("nomeEmpresa", "Empresa confidencial"),
                "cidade":  municipio if municipio else cidade_formatada,
                "salario": v.get("salario", v.get("remuneracao", "A combinar")),
                "link":    "https://empregabrasil.mte.gov.br",
                "fonte":   "Emprega Brasil (Gov. Federal)"
            })
    except Exception:
        pass

    # 2. Complementa com vagas do Indeed Brasil e Gupy (links diretos)
    area_encoded  = urllib.parse.quote(area_limpa)
    cidade_encoded = urllib.parse.quote(cidade_formatada)

    vagas_complemento = [
        {
            "cargo":   f"{area_limpa} — Vagas no Indeed",
            "empresa": "Múltiplas empresas",
            "cidade":  cidade_formatada,
            "salario": "Vários salários",
            "link":    f"https://br.indeed.com/jobs?q={area_encoded}&l={cidade_encoded}%2C+AM&rbl={cidade_encoded}&jlid=&sort=date",
            "fonte":   "Indeed Brasil"
        },
        {
            "cargo":   f"{area_limpa} — Vagas no Gupy",
            "empresa": "Múltiplas empresas",
            "cidade":  cidade_formatada,
            "salario": "Vários salários",
            "link":    f"https://portal.gupy.io/job-search/term={area_encoded}",
            "fonte":   "Gupy"
        },
        {
            "cargo":   "Jovem Aprendiz — Programa Federal",
            "empresa": "CIEE / Parceiros",
            "cidade":  cidade_formatada,
            "salario": "Salário mínimo",
            "link":    f"https://www.ciee.org.br/vaga-de-emprego/vagas?q={area_encoded}&l={cidade_encoded}",
            "fonte":   "CIEE"
        },
        {
            "cargo":   f"{area_limpa} — Vagas no Catho",
            "empresa": "Múltiplas empresas",
            "cidade":  cidade_formatada,
            "salario": "A combinar",
            "link":    f"https://www.catho.com.br/vagas/{urllib.parse.quote(area_limpa.lower())}/{urllib.parse.quote(cidade_formatada.lower())}/",
            "fonte":   "Catho"
        },
        {
            "cargo":   f"{area_limpa} — SINE {cidade_formatada}",
            "empresa": "SINE — Sistema Nacional de Empregos",
            "cidade":  cidade_formatada,
            "salario": "A combinar",
            "link":    "https://empregabrasil.mte.gov.br",
            "fonte":   "Emprega Brasil (Gov. Federal)"
        },
    ]

    # Mescla: primeiro as do governo, depois complemento
    for vc in vagas_complemento:
        if len(vagas) < 8:
            vagas.append(vc)

    return vagas[:8]


# ─────────────────────────────────────────────
# GERAR CONTEÚDO COM IA (Claude)
# ─────────────────────────────────────────────
def gerar_com_ia(dados: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return fallback_sem_ia(dados)

    area   = dados.get("areas", "Administrativo").split(",")[0].strip()
    cidade = dados.get("cidade", "Manaus, AM")

    prompt = f"""Você é especialista em RH para primeiro emprego no Brasil. Gere um pacote completo para:

Nome: {dados.get('nome')}
Cidade: {cidade} (BRASIL — só gere vagas brasileiras)
Email: {dados.get('email')}
Telefone: {dados.get('telefone')}
Escolaridade: {dados.get('escolaridade')}
Área: {dados.get('areas')}
Habilidades: {dados.get('habilidades')}
Experiências: {dados.get('experiencias')}
Sobre: {dados.get('sobre')}
Objetivo: {dados.get('objetivo')}

Gere um JSON com estas chaves EXATAS (sem markdown):
{{
  "cv_html": "HTML do currículo com classes: cv-name, cv-role, cv-contact, cv-sec, cv-text, cv-skills, cv-skill",
  "linkedin": {{
    "titulo": "título para o LinkedIn (máx 120 chars)",
    "sobre": "texto para a seção Sobre do LinkedIn (3-4 parágrafos envolventes)"
  }},
  "email_candidatura": "email completo pronto para enviar ao RH (assunto não incluso)",
  "dicas_entrevista": ["dica 1 personalizada", "dica 2", "dica 3", "dica 4", "dica 5"]
}}

IMPORTANTE: cv_html deve ter seções completas: objetivo, formação, habilidades, experiências, perfil pessoal."""

    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 3000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    )

    with urllib.request.urlopen(req, timeout=40) as resp:
        result = json.loads(resp.read().decode())

    text    = result["content"][0]["text"]
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def fallback_sem_ia(dados: dict) -> dict:
    area = dados.get("areas", "Administrativo").split(",")[0].strip()
    nome = dados.get("nome", "Candidato")
    return {
        "cv_html": f"""
            <div class="cv-name">{nome}</div>
            <div class="cv-role">{area} · Primeiro emprego</div>
            <div class="cv-contact">
                <span>📍 {dados.get('cidade')}</span>
                <span>📧 {dados.get('email')}</span>
                <span>📱 {dados.get('telefone')}</span>
            </div>
            <div class="cv-sec">Objetivo</div>
            <div class="cv-text">{dados.get('objetivo')}</div>
            <div class="cv-sec">Formação</div>
            <div class="cv-text"><strong>{dados.get('escolaridade')}</strong></div>
            <div class="cv-sec">Habilidades</div>
            <div class="cv-skills">{''.join(f'<span class="cv-skill">{h.strip()}</span>' for h in dados.get('habilidades','').split(','))}</div>
            <div class="cv-sec">Experiências</div>
            <div class="cv-text">{dados.get('experiencias')}</div>
            <div class="cv-sec">Sobre mim</div>
            <div class="cv-text">{dados.get('sobre')}</div>
        """,
        "linkedin": {
            "titulo": f"{area} | Buscando primeiro emprego | {dados.get('cidade')}",
            "sobre":  f"{dados.get('sobre')} Busco primeira oportunidade em {area}."
        },
        "email_candidatura": f"Prezado(a) recrutador(a),\n\nVenho me candidatar à vaga de {area}.\n{dados.get('sobre')}\n\nAtenciosamente,\n{nome}\n{dados.get('telefone')}",
        "dicas_entrevista": [
            f"Prepare exemplos de quando você demonstrou {dados.get('habilidades','').split(',')[0].strip()}",
            "Chegue 10 minutos antes da entrevista",
            "Pesquise a empresa antes de ir",
            "Prepare resposta para 'fale sobre você'",
            "No final, pergunte sobre os próximos passos"
        ]
    }


# ─────────────────────────────────────────────
# HANDLER VERCEL
# ─────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length))

        try:
            # 1. Gera conteúdo com IA
            ia = gerar_com_ia(body)

            # 2. Busca vagas SOMENTE no Brasil
            vagas = buscar_vagas_brasil(
                cidade = body.get("cidade", "Manaus, AM"),
                area   = body.get("areas",  "Administrativo")
            )

            resposta = {
                "cv_html":            ia.get("cv_html", ""),
                "linkedin":           ia.get("linkedin", {}),
                "email_candidatura":  ia.get("email_candidatura", ""),
                "dicas_entrevista":   ia.get("dicas_entrevista", []),
                "vagas":              vagas
            }
            self._json(200, resposta)

        except Exception as e:
            self._json(500, {"erro": str(e)})

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status, data):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type",   "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass
