"""
EmpregaAI v3 — Backend Completo
- Vagas com links diretos funcionais (sem login)
- Foto no currículo
- IA de chance de contratação
- Links corrigidos: Indeed BR, LinkedIn, Catho, InfoJobs, SINE
"""

import json
import os
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler


def montar_links_vagas(cidade: str, area: str) -> list:
    """
    Gera links diretos de busca já filtrados por cidade e área.
    Todos funcionam sem login e abrem direto na listagem de vagas.
    """
    area_limpa = area.split(",")[0]
    for emoji in ["💼","💻","📊","🎨","🛒","🤝","📦","🏥","📣","🔧"]:
        area_limpa = area_limpa.replace(emoji, "")
    area_limpa   = area_limpa.strip()
    cidade_limpa = cidade.split(",")[0].strip()
    estado       = cidade.split(",")[1].strip() if "," in cidade else "AM"

    a = urllib.parse.quote(area_limpa)
    c = urllib.parse.quote(cidade_limpa)
    e = urllib.parse.quote(estado.strip())

    return [
        {
            "cargo":   f"Vagas de {area_limpa} — Indeed Brasil",
            "empresa": "Múltiplas empresas",
            "cidade":  cidade_limpa,
            "salario": "Vários",
            "link":    f"https://br.indeed.com/jobs?q={a}&l={c}%2C+{e}&sort=date&fromage=14",
            "fonte":   "Indeed Brasil",
            "descricao": "Portal líder em vagas no Brasil — atualizado diariamente"
        },
        {
            "cargo":   f"Vagas de {area_limpa} — LinkedIn",
            "empresa": "Múltiplas empresas",
            "cidade":  cidade_limpa,
            "salario": "Vários",
            "link":    f"https://www.linkedin.com/jobs/search/?keywords={a}&location={c}%2C%20{e}%2C%20Brasil&f_TPR=r604800&sortBy=DD",
            "fonte":   "LinkedIn Vagas",
            "descricao": "Maior rede profissional — muitas vagas exclusivas aqui"
        },
        {
            "cargo":   f"Vagas de {area_limpa} — Catho",
            "empresa": "Múltiplas empresas",
            "cidade":  cidade_limpa,
            "salario": "Vários",
            "link":    f"https://www.catho.com.br/vagas/?q={a}&where={c}",
            "fonte":   "Catho",
            "descricao": "Um dos maiores sites de emprego do Brasil"
        },
        {
            "cargo":   f"Vagas de {area_limpa} — InfoJobs",
            "empresa": "Múltiplas empresas",
            "cidade":  cidade_limpa,
            "salario": "Vários",
            "link":    f"https://www.infojobs.com.br/empregos-em-{urllib.parse.quote(cidade_limpa.lower())}/cargo_{urllib.parse.quote(area_limpa.lower())}.aspx",
            "fonte":   "InfoJobs",
            "descricao": "Muitas vagas para primeiro emprego e jovem aprendiz"
        },
        {
            "cargo":   f"Jovem Aprendiz em {cidade_limpa} — CIEE",
            "empresa": "CIEE",
            "cidade":  cidade_limpa,
            "salario": "Salário mínimo",
            "link":    f"https://portal.ciee.org.br/candidato/vagas/?q={a}&cidade={c}",
            "fonte":   "CIEE",
            "descricao": "Programa oficial de jovem aprendiz — primeiro emprego garantido"
        },
        {
            "cargo":   f"Vagas de {area_limpa} — Sine Fácil",
            "empresa": "SINE — Governo Federal",
            "cidade":  cidade_limpa,
            "salario": "A combinar",
            "link":    f"https://sinefacil.com.br/vagas?q={a}&location={c}",
            "fonte":   "Sine Fácil",
            "descricao": "App oficial do SINE — vagas do governo sem burocracia"
        },
        {
            "cargo":   f"Vagas de {area_limpa} — Trabalha Brasil",
            "empresa": "Múltiplas empresas",
            "cidade":  cidade_limpa,
            "salario": "A combinar",
            "link":    f"https://www.trabalhabrasil.com.br/vagas-empregos-em-{urllib.parse.quote(cidade_limpa.lower())}/{urllib.parse.quote(area_limpa.lower())}",
            "fonte":   "Trabalha Brasil",
            "descricao": "Portal especializado em vagas para iniciantes"
        },
        {
            "cargo":   f"Vagas de {area_limpa} — Vagas.com",
            "empresa": "Múltiplas empresas",
            "cidade":  cidade_limpa,
            "salario": "A combinar",
            "link":    f"https://www.vagas.com.br/vagas-de-{urllib.parse.quote(area_limpa.lower())}+em+{urllib.parse.quote(cidade_limpa.lower())}",
            "fonte":   "Vagas.com",
            "descricao": "Site tradicional com milhares de vagas em todo Brasil"
        },
    ]


def gerar_com_ia(dados: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return fallback_sem_ia(dados)

    area   = dados.get("areas", "Administrativo").split(",")[0].strip()
    cidade = dados.get("cidade", "Manaus, AM")
    foto_b64 = dados.get("foto_b64", "")  # base64 da foto se houver

    # Monta seção de foto no HTML se existir
    foto_html = ""
    if foto_b64:
        foto_html = f'<img src="data:image/jpeg;base64,{foto_b64}" style="width:90px;height:90px;border-radius:50%;object-fit:cover;float:right;margin-left:20px;border:3px solid #e8521a;" />'

    prompt = f"""Você é especialista em RH para primeiro emprego no Brasil.

Gere um pacote completo para este candidato:
Nome: {dados.get('nome')}
Cidade: {cidade} (Brasil)
Email: {dados.get('email')}
Telefone: {dados.get('telefone')}
Escolaridade: {dados.get('escolaridade')}
Área: {dados.get('areas')}
Habilidades: {dados.get('habilidades')}
Experiências: {dados.get('experiencias')}
Sobre: {dados.get('sobre')}
Objetivo: {dados.get('objetivo')}
Tem foto: {'Sim' if foto_b64 else 'Não'}

Responda APENAS em JSON válido (sem markdown, sem texto antes ou depois):
{{
  "cv_html": "HTML completo com foto_placeholder onde a foto deve aparecer, usando classes: cv-name, cv-role, cv-contact, cv-sec, cv-text, cv-skills, cv-skill. Inclua seções: objetivo, formação, habilidades, experiências, sobre mim",
  "linkedin": {{
    "titulo": "título LinkedIn impactante (máx 120 chars)",
    "sobre": "texto Sobre do LinkedIn (3 parágrafos, envolvente e profissional)"
  }},
  "email_candidatura": "email completo pronto para enviar ao RH (sem assunto)",
  "dicas_entrevista": ["dica 1 personalizada para {area}", "dica 2", "dica 3", "dica 4", "dica 5"],
  "analise_contratacao": {{
    "porcentagem": 72,
    "nivel": "Bom",
    "pontos_fortes": ["ponto 1", "ponto 2", "ponto 3"],
    "pontos_melhorar": ["melhoria 1", "melhoria 2"],
    "resumo": "frase motivacional personalizada de 1 linha"
  }}
}}"""

    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 3500,
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

    with urllib.request.urlopen(req, timeout=40) as resp:
        result = json.loads(resp.read().decode())

    text    = result["content"][0]["text"]
    cleaned = text.replace("```json","").replace("```","").strip()
    ia_data = json.loads(cleaned)

    # Injeta foto no cv_html se existir
    if foto_b64 and "foto_placeholder" in ia_data.get("cv_html",""):
        ia_data["cv_html"] = ia_data["cv_html"].replace(
            "foto_placeholder",
            f'<img src="data:image/jpeg;base64,{foto_b64}" style="width:90px;height:90px;border-radius:50%;object-fit:cover;border:3px solid #e8521a;" />'
        )

    return ia_data


def fallback_sem_ia(dados: dict) -> dict:
    area = dados.get("areas","Administrativo").split(",")[0].replace("💼","").replace("💻","").strip()
    nome = dados.get("nome","Candidato")
    foto_b64 = dados.get("foto_b64","")
    foto_tag = f'<img src="data:image/jpeg;base64,{foto_b64}" style="width:90px;height:90px;border-radius:50%;object-fit:cover;border:3px solid #e8521a;float:right;" />' if foto_b64 else ""

    return {
        "cv_html": f"""
            <div style="overflow:hidden">{foto_tag}
            <div class="cv-name">{nome}</div>
            <div class="cv-role">{area} · Primeiro emprego</div>
            <div class="cv-contact">
                <span>📍 {dados.get('cidade')}</span>
                <span>📧 {dados.get('email')}</span>
                <span>📱 {dados.get('telefone')}</span>
            </div></div>
            <div class="cv-sec">Objetivo</div>
            <div class="cv-text">{dados.get('objetivo')}</div>
            <div class="cv-sec">Formação</div>
            <div class="cv-text"><strong>{dados.get('escolaridade')}</strong></div>
            <div class="cv-sec">Habilidades</div>
            <div class="cv-skills">{''.join(f'<span class="cv-skill">{h.strip()}</span>' for h in dados.get('habilidades','').split(','))}</div>
            <div class="cv-sec">Experiências</div>
            <div class="cv-text">{dados.get('experiencias')}</div>
            <div class="cv-sec">Sobre mim</div>
            <div class="cv-text">{dados.get('sobre')}</div>""",
        "linkedin": {
            "titulo": f"{area} | Buscando primeiro emprego | {dados.get('cidade')}",
            "sobre":  f"{dados.get('sobre')} Busco primeira oportunidade em {area}."
        },
        "email_candidatura": f"Prezado(a) recrutador(a),\n\nVenho me candidatar à vaga de {area}.\n{dados.get('sobre')}\n\nAtenciosamente,\n{nome}\n{dados.get('telefone')}",
        "dicas_entrevista": [
            f"Prepare exemplos de {dados.get('habilidades','').split(',')[0].strip()}",
            "Chegue 10 minutos antes",
            "Pesquise a empresa antes",
            "Prepare resposta para 'fale sobre você'",
            "Pergunte sobre os próximos passos"
        ],
        "analise_contratacao": {
            "porcentagem": 65,
            "nivel": "Bom",
            "pontos_fortes": ["Disposição para aprender", "Habilidades práticas", "Objetivo claro"],
            "pontos_melhorar": ["Adicionar mais experiências", "Completar perfil LinkedIn"],
            "resumo": f"Seu perfil tem boas chances em {area} — continue melhorando!"
        }
    }


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length))

        try:
            ia    = gerar_com_ia(body)
            vagas = montar_links_vagas(
                cidade = body.get("cidade", "Manaus, AM"),
                area   = body.get("areas",  "Administrativo")
            )

            self._json(200, {
                "cv_html":           ia.get("cv_html", ""),
                "linkedin":          ia.get("linkedin", {}),
                "email_candidatura": ia.get("email_candidatura", ""),
                "dicas_entrevista":  ia.get("dicas_entrevista", []),
                "analise_contratacao": ia.get("analise_contratacao", {}),
                "vagas":             vagas
            })

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
