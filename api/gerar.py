"""
EmpregaAI v3 — Backend unificado
Rotas:
  POST /api/gerar    → gera currículo completo
  POST /api/chat     → simulador de entrevista (pergunta por pergunta)
  POST /api/feedback → feedback final da entrevista
  POST /api/chance   → ranking de chance por vaga
"""
import json, os, urllib.request, unicodedata, urllib.parse
from http.server import BaseHTTPRequestHandler

# ─── utils ────────────────────────────────────────────────────────────────────

def slug(txt):
    txt = unicodedata.normalize('NFKD', txt).encode('ascii','ignore').decode('ascii')
    return txt.lower().strip()

def hifenado(txt):
    return slug(txt).replace(' ', '-')

def limpar_area(area):
    for e in ['💼','💻','📊','🎨','🛒','🤝','📦','🏥','📣','🔧']:
        area = area.replace(e, '')
    return area.split(',')[0].strip()

def chamar_ia(prompt, max_tokens=2000):
    api_key = os.environ.get('ANTHROPIC_API_KEY','')
    if not api_key:
        raise Exception('ANTHROPIC_API_KEY não configurada')
    body = json.dumps({
        'model':      'claude-sonnet-4-20250514',
        'max_tokens': max_tokens,
        'messages':   [{'role':'user','content': prompt}]
    }).encode()
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages', data=body,
        headers={'Content-Type':'application/json',
                 'x-api-key':api_key,
                 'anthropic-version':'2023-06-01'}
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        result = json.loads(r.read().decode())
    return result['content'][0]['text']

# ─── vagas ────────────────────────────────────────────────────────────────────

def montar_vagas(cidade, area):
    area_limpa  = limpar_area(area)
    cidade_str  = cidade.split(',')[0].strip()
    estado      = cidade.split(',')[1].strip() if ',' in cidade else 'AM'
    a  = urllib.parse.quote(area_limpa)
    c  = urllib.parse.quote(cidade_str)
    e  = urllib.parse.quote(estado)
    ah = urllib.parse.quote(hifenado(area_limpa))
    ch = urllib.parse.quote(hifenado(cidade_str))
    ci = urllib.parse.quote(cidade_str + ', ' + estado)
    return [
        {'cargo':f'Vagas de {area_limpa} — Indeed','empresa':'Múltiplas','cidade':cidade_str,
         'link':f'https://br.indeed.com/q-{ah}-l-{ci}-vagas.html','fonte':'Indeed Brasil',
         'descricao':'Maior buscador de vagas — resultado filtrado pela sua cidade'},
        {'cargo':f'Vagas de {area_limpa} — LinkedIn','empresa':'Múltiplas','cidade':cidade_str,
         'link':f'https://www.linkedin.com/jobs/search/?keywords={a}&location={c}%2C%20{e}%2C%20Brasil',
         'fonte':'LinkedIn Vagas','descricao':'Vagas exclusivas que não aparecem em outros portais'},
        {'cargo':f'Vagas de {area_limpa} — Catho','empresa':'Múltiplas','cidade':cidade_str,
         'link':f'https://www.catho.com.br/vagas/?q={a}&l={c}%2C+{e}',
         'fonte':'Catho','descricao':'Um dos maiores portais de emprego do Brasil'},
        {'cargo':f'Vagas de {area_limpa} em {cidade_str} — InfoJobs','empresa':'Múltiplas','cidade':cidade_str,
         'link':f'https://www.infojobs.com.br/empregos-em-{ch},-{urllib.parse.quote(estado.lower())}.aspx',
         'fonte':'InfoJobs','descricao':'Busca direta por cidade — resultado da sua região'},
        {'cargo':f'Vagas de {area_limpa} — Gupy','empresa':'Grandes empresas','cidade':cidade_str,
         'link':f'https://portal.gupy.io/job-search/term={a}',
         'fonte':'Gupy','descricao':'Ambev, iFood, Nubank e outras grandes empresas'},
        {'cargo':f'Vagas de {area_limpa} — Empregos.com.br','empresa':'Múltiplas','cidade':cidade_str,
         'link':f'https://www.empregos.com.br/vagas/{ch}/{ah}',
         'fonte':'Empregos.com.br','descricao':'Forte em vagas locais e pequenas empresas'},
        {'cargo':f'Vagas de {area_limpa} — Vagas.com','empresa':'Múltiplas','cidade':cidade_str,
         'link':f'https://www.vagas.com.br/vagas-de-{ah}+em+{ch}',
         'fonte':'Vagas.com','descricao':'Portal consolidado com vagas verificadas'},
        {'cargo':f'Vagas de {area_limpa} — Curriculum.com.br','empresa':'Múltiplas','cidade':cidade_str,
         'link':f'https://www.curriculum.com.br/vagas/?term={a}&cidade={c}&estado={e}',
         'fonte':'Curriculum.com.br','descricao':'9 milhões de profissionais — forte no Norte/Nordeste'},
    ]

# ─── rota: gerar currículo ─────────────────────────────────────────────────────

def rota_gerar(dados):
    area         = limpar_area(dados.get('areas','Administrativo'))
    cidade       = dados.get('cidade','Manaus, AM')
    esc          = dados.get('escolaridade','')
    ano          = dados.get('ano_conclusao','')
    formacao     = esc + (' — '+ano if ano else '')

    prompt = f"""Você é especialista em RH e redação de currículos para primeiro emprego no Brasil.
Gere um pacote profissional RICO e DETALHADO para este candidato.

DADOS:
Nome: {dados.get('nome')}  |  Cidade: {cidade}
Email: {dados.get('email')}  |  Telefone: {dados.get('telefone')}
Formação: {formacao}  |  Área: {dados.get('areas')}
Habilidades: {dados.get('habilidades')}
Experiências (use os períodos EXATOS informados): {dados.get('experiencias')}
Sobre si: {dados.get('sobre')}
Objetivo: {dados.get('objetivo')}

INSTRUÇÕES cv_html:
Use SOMENTE estas classes CSS (já existem no site):
cv-header-info | cv-name | cv-role | cv-contact-line | cv-divider | cv-sec | cv-sec-title | cv-body | cv-bullet | cv-skills-wrap | cv-skill-tag

Estrutura obrigatória:
<div class="cv-header-info">
  <div class="cv-name">NOME EM MAIÚSCULO</div>
  <div class="cv-role">Profissional em Início de Carreira | Area1 • Area2</div>
  <div class="cv-contact-line">📍 Cidade | ✉️ email | 📱 tel</div>
</div>
<div class="cv-divider"></div>
[seções: Objetivo Profissional, Formação Acadêmica, Competências e Habilidades, Experiências Complementares, Sobre Mim]

Para cada seção use:
<div class="cv-sec"><div class="cv-sec-title">TITULO</div></div>
<div class="cv-body">texto</div>
Para habilidades: <div class="cv-skills-wrap"><span class="cv-skill-tag">hab</span>...</div>
Para experiências: <div class="cv-bullet">• texto</div>

Objetivo: 2-3 frases ricas e profissionais.
Experiências: bullets detalhados com períodos exatos do usuário.
Sobre mim: 2-3 frases elaboradas.

Responda APENAS JSON válido sem markdown:
{{"cv_html":"...","linkedin":{{"titulo":"...","sobre":"3 parágrafos completos"}},"email_candidatura":"3-4 parágrafos profissionais","dicas_entrevista":["dica detalhada 1","dica detalhada 2","dica detalhada 3","dica detalhada 4","dica detalhada 5"],"analise_contratacao":{{"porcentagem":72,"nivel":"Bom","pontos_fortes":["...","...","..."],"pontos_melhorar":["...","..."],"resumo":"..."}}}}"""

    text    = chamar_ia(prompt, 4000)
    cleaned = text.replace('```json','').replace('```','').strip()
    ia      = json.loads(cleaned)
    vagas   = montar_vagas(cidade, dados.get('areas','Administrativo'))
    return {
        'cv_html':             ia.get('cv_html',''),
        'linkedin':            ia.get('linkedin',{}),
        'email_candidatura':   ia.get('email_candidatura',''),
        'dicas_entrevista':    ia.get('dicas_entrevista',[]),
        'analise_contratacao': ia.get('analise_contratacao',{}),
        'vagas':               vagas
    }

# ─── rota: próxima pergunta do simulador ──────────────────────────────────────

def rota_chat(dados):
    """Gera a próxima pergunta de entrevista"""
    modo     = dados.get('modo','geral')
    area     = dados.get('area','Administrativo')
    desc     = dados.get('descricao_vaga','')
    perguntas= dados.get('perguntas',[])
    respostas= dados.get('respostas',[])

    personalidade = {
        'geral':   'profissional, simpático e encorajador',
        'vaga':    'focado na vaga específica, técnico e criterioso',
        'dificil': 'rigoroso, direto, exigente e com pouca paciência para respostas vagas'
    }.get(modo,'profissional')

    hist = ''
    for i, (p,r) in enumerate(zip(perguntas, respostas)):
        hist += f'\nP{i+1}: {p}\nR{i+1}: {r}\n'

    prompt = f"""Você é um recrutador {personalidade} entrevistando para a área de {area}.
{('Descrição da vaga: '+desc) if desc else ''}

Histórico da entrevista até agora:{hist if hist else ' (início da entrevista)'}

Faça a PRÓXIMA pergunta de entrevista. 
Regras: apenas a pergunta, máximo 2 frases, não repita perguntas já feitas, sem introduções longas."""

    pergunta = chamar_ia(prompt, 300)
    return {'pergunta': pergunta.strip()}

# ─── rota: feedback final ────────────────────────────────────────────────────

def rota_feedback(dados):
    """Gera avaliação completa da entrevista"""
    modo     = dados.get('modo','geral')
    area     = dados.get('area','Administrativo')
    perguntas= dados.get('perguntas',[])
    respostas= dados.get('respostas',[])

    hist = ''
    for i, (p,r) in enumerate(zip(perguntas, respostas)):
        hist += f'\nPergunta {i+1}: {p}\nResposta {i+1}: {r}\n'

    prompt = f"""Analise esta entrevista de emprego para a área de {area} (modo: {modo}).

ENTREVISTA COMPLETA:{hist}

Gere uma avaliação detalhada e honesta. Responda APENAS JSON válido:
{{"nota":8,"nivel":"Muito bom","resumo":"2-3 frases sobre o desempenho geral específicas para as respostas dadas","fortes":["ponto específico 1","ponto específico 2","ponto específico 3"],"melhorar":["ação concreta 1","ação concreta 2"],"dica":"conselho prático e específico de 2-3 frases baseado nas respostas"}}"""

    text    = chamar_ia(prompt, 600)
    cleaned = text.replace('```json','').replace('```','').strip()
    return json.loads(cleaned)

# ─── rota: chance de vaga ─────────────────────────────────────────────────────

def rota_chance(dados):
    """Calcula compatibilidade candidato × vaga"""
    vaga   = dados.get('vaga','')
    perfil = dados.get('perfil','')

    prompt = f"""Você é especialista em recrutamento e seleção. Analise a compatibilidade.

DESCRIÇÃO DA VAGA:
{vaga}

PERFIL DO CANDIDATO:
{perfil if perfil else 'Candidato em início de carreira sem experiência formal definida.'}

Seja honesto e específico. Responda APENAS JSON válido:
{{"porcentagem":72,"nivel":"Compatível","sub":"frase resumindo a compatibilidade","pontos_fortes":["aspecto específico 1","aspecto específico 2","aspecto específico 3"],"pontos_melhorar":["ação concreta 1","ação concreta 2","ação concreta 3"]}}"""

    text    = chamar_ia(prompt, 500)
    cleaned = text.replace('```json','').replace('```','').strip()
    return json.loads(cleaned)

# ─── fallbacks (sem API) ─────────────────────────────────────────────────────

def fallback_gerar(dados):
    area    = limpar_area(dados.get('areas','Administrativo'))
    nome    = dados.get('nome','Candidato')
    cidade  = dados.get('cidade','Manaus, AM')
    habs    = dados.get('habilidades','Comunicação, Organização')
    sobre   = dados.get('sobre','Pessoa dedicada e proativa')
    obj     = dados.get('objetivo','Iniciar carreira profissional')
    esc     = dados.get('escolaridade','Ensino médio completo')
    ano     = dados.get('ano_conclusao','')
    tel     = dados.get('telefone','')
    email   = dados.get('email','')
    formacao= esc+(' — '+ano if ano else '')
    hab1    = habs.split(',')[0].strip()
    chips   = ''.join(f'<span class="cv-skill-tag">{h.strip()}</span>' for h in habs.split(',') if h.strip())
    exp_html= ''
    exp = dados.get('experiencias','')
    if exp and exp.strip():
        for l in exp.replace(';','\n').split('\n'):
            if l.strip(): exp_html += f'<div class="cv-bullet">• {l.strip()}</div>'
    else:
        exp_html = '<div class="cv-bullet">• Iniciando trajetória profissional com disposição para aprender e contribuir.</div>'

    cv_html = f"""<div class="cv-header-info">
  <div class="cv-name">{nome.upper()}</div>
  <div class="cv-role">Profissional em Início de Carreira | {area}</div>
  <div class="cv-contact-line">📍 {cidade} &nbsp;·&nbsp; ✉️ {email} &nbsp;·&nbsp; 📱 {tel}</div>
</div>
<div class="cv-divider"></div>
<div class="cv-sec"><div class="cv-sec-title">Objetivo Profissional</div></div>
<div class="cv-body">Busco minha primeira oportunidade em {area} para desenvolver habilidades e contribuir com resultados positivos. {obj} Tenho grande disposição para aprender, crescer e superar desafios com dedicação e comprometimento.</div>
<div class="cv-sec"><div class="cv-sec-title">Formação Acadêmica</div></div>
<div class="cv-body"><strong>{formacao}</strong></div>
<div class="cv-sec"><div class="cv-sec-title">Competências e Habilidades</div></div>
<div class="cv-skills-wrap">{chips}</div>
<div class="cv-sec"><div class="cv-sec-title">Experiências Complementares</div></div>
<div class="cv-body">{exp_html}</div>
<div class="cv-sec"><div class="cv-sec-title">Sobre Mim</div></div>
<div class="cv-body">{sobre} Comprometido com meu desenvolvimento profissional, com facilidade para trabalho em equipe, comunicação clara e boa capacidade de adaptação.</div>"""

    return {
        'cv_html': cv_html,
        'linkedin': {
            'titulo': f'{area} | Buscando primeiro emprego | {cidade}',
            'sobre':  f'Olá! Sou {nome}, de {cidade}, buscando minha primeira oportunidade em {area}.\n\nTenho {formacao.lower()} e habilidades em {habs}. {sobre}. Estou comprometido com meu crescimento profissional.\n\nEstou disponível para estágio, jovem aprendiz ou primeiro emprego. Vamos conversar!'
        },
        'email_candidatura': f'Prezado(a) Recrutador(a),\n\nVenho manifestar interesse em integrar a equipe de vocês na área de {area}. Sou {nome}, residente em {cidade}, e estou em busca da minha primeira oportunidade profissional.\n\nPossuo {formacao.lower()} e habilidades em {habs}. {sobre}. Acredito que minha dedicação e vontade de aprender podem agregar valor desde o primeiro dia.\n\nEstou disponível para entrevista. Agradeço a atenção.\n\nAtenciosamente,\n{nome}\n{tel} | {email}',
        'dicas_entrevista': [
            f'Pesquise a empresa antes: site, redes sociais, o que ela faz. Mencione algo específico — isso impressiona qualquer recrutador de {area}.',
            f'Prepare "Fale sobre você": nome, formação ({esc}), habilidades em {area} e por que quer trabalhar lá. Ensaie 3 vezes em voz alta.',
            f'Destaque {hab1} com um exemplo real — da escola, família ou voluntariado. Exemplos concretos valem mais que teoria.',
            'Chegue 15 minutos antes, roupas adequadas, sorriso genuíno e postura confiante. A primeira impressão começa antes de falar.',
            'Ao final pergunte: "Quais são os próximos passos?" Demonstra interesse, organização e maturidade profissional.'
        ],
        'analise_contratacao': {
            'porcentagem': 68, 'nivel': 'Bom',
            'pontos_fortes':  ['Disposição para aprender', f'Habilidades em {hab1}', 'Objetivo profissional claro'],
            'pontos_melhorar':['Detalhar experiências com datas e resultados', 'Criar e completar o LinkedIn'],
            'resumo': f'Você está no caminho certo para conseguir sua primeira vaga em {area}!'
        },
        'vagas': montar_vagas(cidade, dados.get('areas','Administrativo'))
    }

FALLBACK_PERGUNTAS = {
    'geral':   ['Me conte sobre você e por que tem interesse nessa área.','Quais são suas principais habilidades?','Como você lida com pressão e prazos apertados?','Me dê um exemplo de situação difícil que você resolveu.','Onde você se vê profissionalmente daqui a 2 anos?'],
    'dificil': ['Por que eu deveria te contratar em vez de alguém com experiência?','Quais são seus 3 maiores defeitos profissionais?','Me convença em 60 segundos por que você é a melhor escolha.','O que você sabe sobre essa área além do básico?','Se errar no primeiro mês, o que você faria?'],
    'vaga':    ['O que te atraiu nessa vaga específica?','Que habilidades suas se encaixam nessa posição?','Como lidaria com o volume de trabalho descrito?','Você tem experiência relacionada ao descrito?','Por que nossa empresa e não a concorrência?']
}

def fallback_chat(dados):
    modo     = dados.get('modo','geral')
    respostas= dados.get('respostas',[])
    idx      = len(respostas) % len(FALLBACK_PERGUNTAS.get(modo, FALLBACK_PERGUNTAS['geral']))
    pergunta = FALLBACK_PERGUNTAS.get(modo, FALLBACK_PERGUNTAS['geral'])[idx]
    return {'pergunta': pergunta}

def fallback_feedback(dados):
    respostas = dados.get('respostas',[])
    nota = min(10, max(4, sum(1 for r in respostas if len(r)>40)*2 + 2))
    return {
        'nota': nota, 'nivel': 'Bom trabalho' if nota>=6 else 'Continue praticando',
        'resumo': 'Você completou a simulação! Cada treino te deixa mais próximo da vaga.',
        'fortes': ['Completou todas as perguntas','Demonstrou disposição','Manteve o foco até o final'],
        'melhorar': ['Use exemplos concretos e específicos','Seja mais detalhado nas respostas'],
        'dica': 'Pratique responder em voz alta para ganhar fluidez e confiança nas entrevistas.'
    }

def fallback_chance(dados):
    return {
        'porcentagem': 65, 'nivel': 'Compatível',
        'sub': 'Você tem potencial para esta vaga. Continue melhorando seu perfil.',
        'pontos_fortes': ['Candidato ativo e engajado','Demonstrou interesse na vaga'],
        'pontos_melhorar': ['Complete seu perfil com habilidades relevantes','Pesquise mais sobre a empresa','Adapte seu currículo para a vaga']
    }

# ─── HTTP handler ─────────────────────────────────────────────────────────────

ROTAS = {
    '/api/gerar':    (rota_gerar,    fallback_gerar),
    '/api/chat':     (rota_chat,     fallback_chat),
    '/api/feedback': (rota_feedback, fallback_feedback),
    '/api/chance':   (rota_chance,   fallback_chance),
}

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    def do_POST(self):
        rota = self.path.split('?')[0]
        if rota not in ROTAS:
            self._json(404, {'erro': 'Rota não encontrada'}); return
        fn_ia, fn_fb = ROTAS[rota]
        length = int(self.headers.get('Content-Length',0))
        body   = json.loads(self.rfile.read(length)) if length else {}
        try:
            resultado = fn_ia(body)
        except Exception as ex:
            print(f'[{rota}] IA falhou: {ex} — usando fallback')
            try:
                resultado = fn_fb(body)
            except Exception as ex2:
                self._json(500, {'erro': str(ex2)}); return
        self._json(200, resultado)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')

    def _json(self, status, data):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status); self._cors()
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers(); self.wfile.write(payload)

    def log_message(self, *a): pass
