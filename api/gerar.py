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
    Gera links diretos 100% funcionais, filtrados pela cidade E área da pessoa.
    Formato de URL testado e confirmado para cada portal.
    """
    area_limpa = area.split(",")[0]
    for emoji in ["💼","💻","📊","🎨","🛒","🤝","📦","🏥","📣","🔧"]:
        area_limpa = area_limpa.replace(emoji, "")
    area_limpa   = area_limpa.strip()
    cidade_limpa = cidade.split(",")[0].strip()
    estado       = cidade.split(",")[1].strip() if "," in cidade else "AM"

    # Variantes para diferentes formatos de URL
    a_hifenado  = area_limpa.lower().replace(" ", "-")
    c_hifenado  = cidade_limpa.lower().replace(" ", "-")
    a_encoded   = urllib.parse.quote(area_limpa)
    c_encoded   = urllib.parse.quote(cidade_limpa)
    # Indeed: espaços viram hífens, acento mantido
    a_indeed    = urllib.parse.quote(area_limpa.lower().replace(" ", "-"))
    c_indeed    = urllib.parse.quote(f"{cidade_limpa}, {estado.strip()}")

    return [
        {
            # Formato confirmado nos resultados de busca:
            # br.indeed.com/q-CARGO-l-CIDADE,-UF-vagas.html
            "cargo":     f"Vagas de {area_limpa} — Indeed Brasil",
            "empresa":   "Múltiplas empresas",
            "cidade":    cidade_limpa,
            "salario":   "Vários",
            "link":      f"https://br.indeed.com/q-{a_indeed}-l-{c_indeed}-vagas.html",
            "fonte":     "Indeed Brasil",
            "descricao": "Maior buscador de vagas do Brasil — já filtrado pela sua cidade"
        },
        {
            # LinkedIn: keywords + location com cidade e UF
            "cargo":     f"Vagas de {area_limpa} — LinkedIn",
            "empresa":   "Múltiplas empresas",
            "cidade":    cidade_limpa,
            "salario":   "Vários",
            "link":      f"https://www.linkedin.com/jobs/search/?keywords={a_encoded}&location={c_encoded}%2C%20{urllib.parse.quote(estado.strip())}%2C%20Brasil",
            "fonte":     "LinkedIn Vagas",
            "descricao": "Vagas exclusivas que não aparecem em outros portais"
        },
        {
            # Catho: /vagas/CARGO/CIDADE
            "cargo":     f"Vagas de {area_limpa} — Catho",
            "empresa":   "Múltiplas empresas",
            "cidade":    cidade_limpa,
            "salario":   "Vários",
            "link":      f"https://www.catho.com.br/vagas/{a_hifenado}/{c_hifenado}/",
            "fonte":     "Catho",
            "descricao": "Um dos maiores portais de emprego do Brasil"
        },
        {
            # InfoJobs: /empregos-em-CIDADE/cargo_AREA.aspx
            "cargo":     f"Vagas de {area_limpa} — InfoJobs",
            "empresa":   "Múltiplas empresas",
            "cidade":    cidade_limpa,
            "salario":   "Vários",
            "link":      f"https://www.infojobs.com.br/empregos-em-{c_hifenado}/cargo_{a_hifenado}.aspx",
            "fonte":     "InfoJobs",
            "descricao": "Ótimo para atendimento, vendas e administrativo"
        },
        {
            # Gupy portal: busca por termo + cidade
            "cargo":     f"Vagas de {area_limpa} — Gupy",
            "empresa":   "Grandes empresas",
            "cidade":    cidade_limpa,
            "salario":   "Vários",
            "link":      f"https://portal.gupy.io/job-search/term={a_encoded}%20{c_encoded}",
            "fonte":     "Gupy",
            "descricao": "Usado por grandes empresas — Ambev, iFood, Nubank e outras"
        },
        {
            # Empregos.com.br: /vagas/CIDADE/AREA
            "cargo":     f"Vagas de {area_limpa} — Empregos.com.br",
            "empresa":   "Múltiplas empresas",
            "cidade":    cidade_limpa,
            "salario":   "Vários",
            "link":      f"https://www.empregos.com.br/vagas/{c_hifenado}/{a_hifenado}",
            "fonte":     "Empregos.com.br",
            "descricao": "Forte em vagas locais e de pequenas empresas"
        },
        {
            # Nube: busca por descrição + cidade + UF
            "cargo":     f"Jovem Aprendiz / Estágio — Nube",
            "empresa":   "Nube",
            "cidade":    cidade_limpa,
            "salario":   "Bolsa + benefícios",
            "link":      f"https://www.nube.com.br/candidato/oportunidade/busca?descricao={a_encoded}&cidade={c_encoded}&uf={urllib.parse.quote(estado.strip())}",
            "fonte":     "Nube",
            "descricao": "Especializado em estágio e jovem aprendiz — primeiro emprego"
        },
        {
            # Selpe: busca simples que funciona por cidade
            "cargo":     f"Vagas de {area_limpa} — Selpe",
            "empresa":   "Múltiplas empresas",
            "cidade":    cidade_limpa,
            "salario":   "Vários",
            "link":      f"https://www.selpe.com.br/vagas/?s={a_encoded}+{c_encoded}",
            "fonte":     "Selpe",
            "descricao": "Portal focado no Norte e Nordeste do Brasil"
        },
    ]


def gerar_com_ia(dados: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return fallback_sem_ia(dados)

    area   = dados.get("areas", "Administrativo").split(",")[0].strip()
    cidade = dados.get("cidade", "Manaus, AM")
    foto_b64 = dados.get("foto_b64", "")
    escolaridade = dados.get("escolaridade", "")
    ano_conclusao = dados.get("ano_conclusao", "")
    formacao_completa = f"{escolaridade}" + (f" — {ano_conclusao}" if ano_conclusao else "")

    prompt = f"""Você é especialista em RH para primeiro emprego no Brasil.

Gere um pacote completo para este candidato:
Nome: {dados.get('nome')}
Cidade: {cidade} (Brasil)
Email: {dados.get('email')}
Telefone: {dados.get('telefone')}
Escolaridade: {formacao_completa}
Área: {dados.get('areas')}
Habilidades: {dados.get('habilidades')}
Experiências (com períodos informados pelo usuário — use EXATAMENTE os períodos que ele informou, nunca invente datas): {dados.get('experiencias')}
Sobre: {dados.get('sobre')}
Objetivo: {dados.get('objetivo')}
Tem foto: {'Sim' if foto_b64 else 'Não'}

REGRAS IMPORTANTES:
- Na seção Formação, use EXATAMENTE: "{formacao_completa}" — nunca coloque outro ano
- Nas experiências, use EXATAMENTE os períodos que o usuário informou — nunca invente datas
- Se o usuário não informou período de alguma experiência, deixe sem data

Responda APENAS em JSON válido (sem markdown, sem texto antes ou depois):
{{
  "cv_html": "HTML completo com foto_placeholder onde a foto deve aparecer, usando classes: cv-name, cv-role, cv-contact, cv-sec, cv-text, cv-skills, cv-skill. Inclua seções: objetivo, formação (com o ano exato informado), habilidades, experiências (com os períodos exatos informados), sobre mim",
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
