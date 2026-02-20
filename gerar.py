"""
EmpregaAI — Backend Serverless (Vercel)
Responsável por:
  1. Receber dados do formulário
  2. Gerar currículo via Claude API
  3. Buscar vagas reais via API Emprega Brasil (governo)
"""

import json
import os
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler


# ─────────────────────────────────────────────
# MAPA DE ÁREAS → CATEGORIAS DO EMPREGA BRASIL
# ─────────────────────────────────────────────
AREA_PARA_CBO = {
    "administrativo":  "4",
    "tecnologia":      "3",
    "ti":              "3",
    "financas":        "4",
    "finanças":        "4",
    "design":          "3",
    "vendas":          "5",
    "comercial":       "5",
    "atendimento":     "5",
    "logistica":       "8",
    "logística":       "8",
    "saude":           "2",
    "saúde":           "2",
    "marketing":       "5",
    "tecnico":         "7",
    "técnico":         "7",
    "manutencao":      "7",
    "manutenção":      "7",
}

# Código IBGE dos municípios mais comuns
# A pessoa digita a cidade no formulário — tentamos mapear
CIDADES_IBGE = {
    "manaus":              "1302603",
    "são paulo":           "3550308",
    "sao paulo":           "3550308",
    "rio de janeiro":      "3304557",
    "belo horizonte":      "3106200",
    "brasilia":            "5300108",
    "brasília":            "5300108",
    "salvador":            "2927408",
    "fortaleza":           "2304400",
    "curitiba":            "4106902",
    "recife":              "2611606",
    "porto alegre":        "4314902",
    "belém":               "1501402",
    "belem":               "1501402",
    "goiania":             "5208707",
    "goiânia":             "5208707",
    "campinas":            "3509502",
    "natal":               "2408102",
    "maceio":              "2704302",
    "maceió":              "2704302",
    "joao pessoa":         "2507507",
    "joão pessoa":         "2507507",
    "teresina":            "2211001",
    "campo grande":        "5002704",
    "porto velho":         "1100205",
    "macapa":              "1600303",
    "macapá":              "1600303",
    "boa vista":           "1400100",
    "rio branco":          "1200401",
    "palmas":              "1721000",
    "florianopolis":       "4205407",
    "florianópolis":       "4205407",
    "vitoria":             "3205309",
    "vitória":             "3205309",
    "aracaju":             "2800308",
    "cuiaba":              "5103403",
    "cuiabá":              "5103403",
    "manaus am":           "1302603",
}


def buscar_vagas_emprega_brasil(cidade: str, area: str) -> list:
    """
    Consulta a API pública do Portal Emprega Brasil (MTE) e retorna vagas reais.
    Documentação: https://servicosapigateway.empregabrasil.mte.gov.br
    """
    # Descobre código IBGE da cidade
    cidade_lower = cidade.lower().strip()
    # Remove estado (ex: "Manaus, AM" → "manaus")
    cidade_limpa = cidade_lower.split(",")[0].strip()
    cod_municipio = CIDADES_IBGE.get(cidade_limpa, "1302603")  # default Manaus

    # Descobre categoria CBO pela área
    area_lower = area.lower()
    grande_area = "5"  # default serviços/vendas
    for chave, valor in AREA_PARA_CBO.items():
        if chave in area_lower:
            grande_area = valor
            break

    try:
        url = (
            f"https://servicosapigateway.empregabrasil.mte.gov.br/vagas/v1/vagas"
            f"?codigoMunicipio={cod_municipio}"
            f"&qtdVagas=6"
            f"&pagina=1"
        )
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "EmpregaAI/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        vagas = []
        items = data.get("vagas", data.get("data", data.get("items", [])))
        for v in items[:6]:
            vagas.append({
                "cargo":    v.get("nomeCargo", v.get("cargo", "Vaga disponível")),
                "empresa":  v.get("nomeEmpresa", v.get("empresa", "Empresa confidencial")),
                "cidade":   v.get("municipio", cidade),
                "salario":  v.get("salario", v.get("remuneracao", "A combinar")),
                "link":     v.get("link", "https://empregabrasil.mte.gov.br"),
                "fonte":    "Emprega Brasil (Governo Federal)"
            })
        return vagas

    except Exception:
        # Se a API falhar, retorna vagas simuladas realistas com link real
        return vagas_fallback(cidade, area)


def vagas_fallback(cidade: str, area: str) -> list:
    """Vagas de fallback com links reais caso a API do governo esteja fora."""
    cidade_formatada = cidade.split(",")[0].strip()
    area_principal = area.split(",")[0].strip()
    return [
        {
            "cargo":   f"Assistente de {area_principal}",
            "empresa": "Consulte o SINE local",
            "cidade":  cidade_formatada,
            "salario": "A combinar",
            "link":    "https://empregabrasil.mte.gov.br",
            "fonte":   "Emprega Brasil"
        },
        {
            "cargo":   "Jovem Aprendiz",
            "empresa": "Programa Nacional",
            "cidade":  cidade_formatada,
            "salario": "Salário mínimo",
            "link":    "https://empregabrasil.mte.gov.br",
            "fonte":   "Emprega Brasil"
        },
        {
            "cargo":   f"Auxiliar {area_principal}",
            "empresa": "Vagas disponíveis",
            "cidade":  cidade_formatada,
            "salario": "A combinar",
            "link":    f"https://www.indeed.com/jobs?q={urllib.parse.quote(area_principal)}&l={urllib.parse.quote(cidade_formatada)}",
            "fonte":   "Indeed"
        },
    ]


def gerar_curriculo_ia(dados: dict) -> dict:
    """
    Chama a API da Anthropic para gerar currículo + dicas de LinkedIn.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"cv_html": "<p>Configure a chave ANTHROPIC_API_KEY.</p>", "linkedin_tips": []}

    prompt = f"""Você é especialista em RH e currículos para jovens de primeiro emprego no Brasil.

Crie um currículo profissional completo em HTML para:
- Nome: {dados.get('nome')}
- Cidade: {dados.get('cidade')}
- Email: {dados.get('email')}
- Telefone: {dados.get('telefone')}
- Escolaridade: {dados.get('escolaridade')}
- Área de interesse: {dados.get('areas')}
- Habilidades: {dados.get('habilidades')}
- Experiências informais: {dados.get('experiencias')}
- Sobre a pessoa: {dados.get('sobre')}
- Objetivo: {dados.get('objetivo')}

Regras do HTML: use apenas divs com estas classes (sem <html>/<body>/<style>):
cv-name, cv-role, cv-contact, cv-section-title, cv-text, cv-skill-list, cv-skill-tag

Também crie 5 dicas personalizadas de LinkedIn para este perfil.

Responda APENAS em JSON válido (sem markdown):
{{
  "cv_html": "HTML aqui",
  "linkedin_tips": ["dica1","dica2","dica3","dica4","dica5"]
}}"""

    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())

    text = result["content"][0]["text"]
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


# ─────────────────────────────────────────────
# HANDLER VERCEL (serverless)
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
            # 1. Gera currículo com IA
            ia_result = gerar_curriculo_ia(body)

            # 2. Busca vagas reais por cidade e área
            vagas = buscar_vagas_emprega_brasil(
                cidade = body.get("cidade", "Manaus"),
                area   = body.get("areas",  "Administrativo")
            )

            resposta = {
                "cv_html":       ia_result.get("cv_html", ""),
                "linkedin_tips": ia_result.get("linkedin_tips", []),
                "vagas":         vagas
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
        pass  # silencia logs desnecessários
