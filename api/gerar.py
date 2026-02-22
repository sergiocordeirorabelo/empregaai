"""
EmpregaAI v3 — Backend
- IA gera currículo rico, LinkedIn completo, email profissional
- Fallback local também gera conteúdo rico sem IA
- Vagas com links diretos por cidade/área
- Foto processada só no navegador (não enviada para API)
"""

import json
import os
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler


def limpar_area(area: str) -> str:
    for emoji in ["💼","💻","📊","🎨","🛒","🤝","📦","🏥","📣","🔧"]:
        area = area.replace(emoji, "")
    return area.split(",")[0].strip()


def montar_links_vagas(cidade: str, area: str) -> list:
    area_limpa   = limpar_area(area)
    cidade_limpa = cidade.split(",")[0].strip()
    estado       = cidade.split(",")[1].strip() if "," in cidade else "AM"

    ah = urllib.parse.quote(area_limpa.lower().replace(" ", "-"))
    ch = urllib.parse.quote(cidade_limpa.lower().replace(" ", "-"))
    a  = urllib.parse.quote(area_limpa)
    c  = urllib.parse.quote(cidade_limpa)
    e  = urllib.parse.quote(estado)
    ai = urllib.parse.quote(area_limpa.lower().replace(" ", "-"))
    ci = urllib.parse.quote(cidade_limpa + ", " + estado)

    return [
        {"cargo": "Vagas de "+area_limpa+" — Indeed Brasil",   "empresa": "Múltiplas", "cidade": cidade_limpa, "salario": "Vários", "link": "https://br.indeed.com/q-"+ai+"-l-"+ci+"-vagas.html",                                                              "fonte": "Indeed Brasil",    "descricao": "Maior buscador do Brasil — filtrado pela sua cidade"},
        {"cargo": "Vagas de "+area_limpa+" — LinkedIn",        "empresa": "Múltiplas", "cidade": cidade_limpa, "salario": "Vários", "link": "https://www.linkedin.com/jobs/search/?keywords="+a+"&location="+c+"%2C%20"+e+"%2C%20Brasil",                         "fonte": "LinkedIn Vagas",   "descricao": "Vagas exclusivas que não aparecem em outros portais"},
        {"cargo": "Vagas de "+area_limpa+" — Catho",           "empresa": "Múltiplas", "cidade": cidade_limpa, "salario": "Vários", "link": "https://www.catho.com.br/vagas/"+ah+"/"+ch+"/",                                                                      "fonte": "Catho",            "descricao": "Um dos maiores portais de emprego do Brasil"},
        {"cargo": "Vagas de "+area_limpa+" — InfoJobs",        "empresa": "Múltiplas", "cidade": cidade_limpa, "salario": "Vários", "link": "https://www.infojobs.com.br/empregos-em-"+ch+"/cargo_"+ah+".aspx",                                                    "fonte": "InfoJobs",         "descricao": "Ótimo para atendimento, vendas e administrativo"},
        {"cargo": "Vagas de "+area_limpa+" — Gupy",            "empresa": "Grandes",   "cidade": cidade_limpa, "salario": "Vários", "link": "https://portal.gupy.io/job-search/term="+a+"%20"+c,                                                                   "fonte": "Gupy",             "descricao": "Ambev, iFood, Nubank e outras grandes empresas"},
        {"cargo": "Vagas de "+area_limpa+" — Empregos.com.br", "empresa": "Múltiplas", "cidade": cidade_limpa, "salario": "Vários", "link": "https://www.empregos.com.br/vagas/"+ch+"/"+ah,                                                                        "fonte": "Empregos.com.br",  "descricao": "Forte em vagas locais e pequenas empresas"},
        {"cargo": "Jovem Aprendiz / Estágio — Nube",           "empresa": "Nube",      "cidade": cidade_limpa, "salario": "Bolsa",  "link": "https://www.nube.com.br/candidato/oportunidade/busca?descricao="+a+"&cidade="+c+"&uf="+e,                              "fonte": "Nube",             "descricao": "Especializado em estágio e jovem aprendiz"},
        {"cargo": "Vagas de "+area_limpa+" — Selpe",           "empresa": "Múltiplas", "cidade": cidade_limpa, "salario": "Vários", "link": "https://www.selpe.com.br/vagas/?s="+a+"+"+c,                                                                          "fonte": "Selpe",            "descricao": "Portal focado no Norte e Nordeste do Brasil"},
    ]


def gerar_com_ia(dados: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return fallback_sem_ia(dados)

    area          = limpar_area(dados.get("areas", "Administrativo"))
    cidade        = dados.get("cidade", "Manaus, AM")
    escolaridade  = dados.get("escolaridade", "")
    ano_conclusao = dados.get("ano_conclusao", "")
    formacao      = escolaridade + (" — " + ano_conclusao if ano_conclusao else "")

    prompt = (
        "Você é especialista em RH e redação de currículos para primeiro emprego no Brasil.\n"
        "Sua missão: transformar informações simples em um pacote profissional COMPLETO e RICO.\n\n"
        "DADOS DO CANDIDATO:\n"
        f"Nome: {dados.get('nome')}\n"
        f"Cidade: {cidade}\n"
        f"Email: {dados.get('email')}\n"
        f"Telefone: {dados.get('telefone')}\n"
        f"Escolaridade: {formacao}\n"
        f"Área desejada: {dados.get('areas')}\n"
        f"Habilidades: {dados.get('habilidades')}\n"
        f"Experiências (use EXATAMENTE os períodos informados, nunca invente datas): {dados.get('experiencias')}\n"
        f"Sobre si mesmo: {dados.get('sobre')}\n"
        f"Objetivo: {dados.get('objetivo')}\n\n"
        "INSTRUÇÕES:\n"
        "1. cv_html: Currículo RICO usando classes cv-name, cv-role, cv-contact, cv-sec, cv-text, cv-skills, cv-skill.\n"
        f"   - Formação: use EXATAMENTE '{formacao}'\n"
        "   - Objetivo: 2-3 frases elaboradas\n"
        "   - Experiências: expanda com bullet points descrevendo atividades profissionais\n"
        "   - Sobre mim: 2-3 frases elaboradas\n"
        "2. linkedin.sobre: 3 parágrafos completos e envolventes\n"
        "3. email_candidatura: email profissional de 3-4 parágrafos completo\n"
        f"4. dicas_entrevista: 5 dicas detalhadas e específicas para {area}\n\n"
        "Responda APENAS em JSON válido sem markdown:\n"
        '{"cv_html":"...","linkedin":{"titulo":"...","sobre":"..."},'
        '"email_candidatura":"...","dicas_entrevista":["..."],'
        '"analise_contratacao":{"porcentagem":72,"nivel":"Bom","pontos_fortes":["..."],"pontos_melhorar":["..."],"resumo":"..."}}'
    )

    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
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

    with urllib.request.urlopen(req, timeout=45) as resp:
        result = json.loads(resp.read().decode())

    text    = result["content"][0]["text"]
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def fallback_sem_ia(dados: dict) -> dict:
    area   = limpar_area(dados.get("areas", "Administrativo"))
    nome   = dados.get("nome", "Candidato")
    cidade = dados.get("cidade", "Manaus, AM")
    habs   = dados.get("habilidades", "Comunicacao, Organizacao")
    exp    = dados.get("experiencias", "")
    sobre  = dados.get("sobre", "Pessoa dedicada e proativa")
    obj    = dados.get("objetivo", "Iniciar carreira profissional")
    esc    = dados.get("escolaridade", "Ensino medio completo")
    ano    = dados.get("ano_conclusao", "")
    tel    = dados.get("telefone", "")
    email  = dados.get("email", "")
    formacao = esc + (" — " + ano if ano else "")
    hab1   = habs.split(",")[0].strip() if habs else "comunicacao"
    chips  = "".join('<span class="cv-skill">'+h.strip()+'</span>' for h in habs.split(",") if h.strip())

    # Expande experiencias em bullets
    exp_html = ""
    if exp and exp.strip() and exp.strip() not in ("Sem experiencia formal", "Sem experiência formal"):
        for linha in [l.strip() for l in exp.replace(";", "\n").split("\n") if l.strip()]:
            exp_html += "<p style='margin:0 0 8px 0'>• " + linha + "</p>"
    else:
        exp_html = "<p style='margin:0 0 8px 0'>• Estou iniciando minha trajetória profissional com disposição para aprender e contribuir.</p>"

    cv_html = (
        "<div style='overflow:hidden'>"
        "<div class='cv-name'>" + nome + "</div>"
        "<div class='cv-role'>💼 " + area + " · Primeiro emprego</div>"
        "<div class='cv-contact'><span>📍 " + cidade + "</span><span>📧 " + email + "</span><span>📱 " + tel + "</span></div>"
        "</div>"
        "<div class='cv-sec'>Objetivo Profissional</div>"
        "<div class='cv-text'>Busco minha primeira oportunidade na área de " + area + " para desenvolver minhas habilidades e contribuir com resultados positivos. " + obj + " Tenho grande disposição para aprender, crescer e superar desafios com dedicação e comprometimento.</div>"
        "<div class='cv-sec'>Formação Acadêmica</div>"
        "<div class='cv-text'><strong>" + formacao + "</strong></div>"
        "<div class='cv-sec'>Habilidades</div>"
        "<div class='cv-skills'>" + chips + "</div>"
        "<div class='cv-sec'>Experiências e Atividades</div>"
        "<div class='cv-text'>" + exp_html + "</div>"
        "<div class='cv-sec'>Perfil Pessoal</div>"
        "<div class='cv-text'>" + sobre + " Sou comprometido com meu desenvolvimento profissional e tenho facilidade para trabalhar em equipe, comunicação clara e boa capacidade de adaptação a novos ambientes e desafios.</div>"
    )

    linkedin_sobre = (
        "Olá! Sou " + nome + ", de " + cidade + ", buscando minha primeira oportunidade em " + area + ".\n\n"
        "Tenho " + formacao.lower() + " e habilidades em " + habs + ". "
        "Sou uma pessoa " + sobre.lower().rstrip('.') + " e estou comprometido com meu crescimento profissional.\n\n"
        "Estou disponível para estágio, jovem aprendiz ou primeiro emprego em " + area + ". "
        "Se você tem uma oportunidade ou quer trocar experiências, vamos conversar!"
    )

    email_cand = (
        "Prezado(a) Recrutador(a),\n\n"
        "Venho manifestar meu interesse em integrar a equipe de vocês na área de " + area + ". "
        "Sou " + nome + ", residente em " + cidade + ", e estou em busca da minha primeira oportunidade profissional.\n\n"
        "Possuo " + formacao.lower() + " e desenvolvi habilidades em " + habs + ". "
        + sobre + " Acredito que minha dedicação e vontade de aprender podem agregar valor à empresa desde o primeiro dia.\n\n"
        "Estou disponível para entrevista no horário mais conveniente. Agradeço a atenção e aguardo retorno.\n\n"
        "Atenciosamente,\n" + nome + "\n" + tel + "\n" + email
    )

    dicas = [
        "Pesquise tudo sobre a empresa antes da entrevista: site, redes sociais, o que a empresa faz. Mencione algo que você viu — isso impressiona muito o recrutador de " + area + ".",
        "Prepare sua resposta para 'Fale sobre você': diga seu nome, formação (" + esc + "), principais habilidades em " + area + " e por que quer trabalhar nessa empresa. Ensaie em voz alta.",
        "Destaque sua habilidade em " + hab1 + " com um exemplo real — mesmo da escola, família ou voluntariado. Exemplos concretos valem mais do que teoria.",
        "Chegue 15 minutos antes, com roupa adequada (social ou smart casual), sorriso e postura confiante. A primeira impressão começa antes de você abrir a boca.",
        "Ao final pergunte: 'Quais são os próximos passos do processo seletivo?' Isso demonstra interesse, organização e maturidade profissional."
    ]

    return {
        "cv_html":             cv_html,
        "linkedin":            {"titulo": area + " | Buscando primeiro emprego | " + cidade, "sobre": linkedin_sobre},
        "email_candidatura":   email_cand,
        "dicas_entrevista":    dicas,
        "analise_contratacao": {
            "porcentagem":    68,
            "nivel":          "Bom",
            "pontos_fortes":  ["Disposição para aprender", "Habilidades em " + hab1, "Objetivo profissional claro"],
            "pontos_melhorar":["Detalhar experiências com datas e resultados", "Criar e completar o LinkedIn"],
            "resumo":         "Você está no caminho certo para conseguir sua primeira vaga em " + area + "!"
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
            vagas = montar_links_vagas(cidade=body.get("cidade","Manaus, AM"), area=body.get("areas","Administrativo"))
            self._json(200, {
                "cv_html":             ia.get("cv_html", ""),
                "linkedin":            ia.get("linkedin", {}),
                "email_candidatura":   ia.get("email_candidatura", ""),
                "dicas_entrevista":    ia.get("dicas_entrevista", []),
                "analise_contratacao": ia.get("analise_contratacao", {}),
                "vagas":               vagas
            })
        except Exception as ex:
            self._json(500, {"erro": str(ex)})

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
