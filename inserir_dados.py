from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Aqui estamos importando as coisas que você criou no arquivo database.py
from database import engine, Colaborador, Certificado

# 1. Preparando a "Sessão" para conversar com o banco
Session = sessionmaker(bind=engine)
sessao = Session()

print("Iniciando o cadastro...")

# 2. Criando um novo Colaborador no Python
novo_colaborador = Colaborador(
    nome_completo="Dr. João da Silva",
    cpf="123.456.789-00",
    funcao="Médico Clínico",
    conselho_numero="CRM 12345",
    setor="Pronto Atendimento"
)

# Adicionamos na sessão e salvamos (commit)
sessao.add(novo_colaborador)
sessao.commit()

print(f"Colaborador {novo_colaborador.nome_completo} salvo com o ID: {novo_colaborador.id}")

# 3. Calculando as datas do Certificado
data_hoje = datetime.now()
# timedelta serve para somar tempo. 3 anos = 1095 dias
data_vencimento = data_hoje + timedelta(days=1095)

# 4. Criando o Certificado vinculado ao colaborador que acabamos de salvar
novo_certificado = Certificado(
    colaborador_id=novo_colaborador.id, # Pegamos o ID gerado automaticamente
    tipo_certificado="A3",
    modalidade_emissao="Presencial",
    data_emissao=data_hoje,
    data_expiracao=data_vencimento,
    status_entrega="Pendente",
    patrimonio_token="TOK-998877"
)

sessao.add(novo_certificado)
sessao.commit()

print(f"Certificado A3 gerado com sucesso!")
print(f"Data de Emissão: {novo_certificado.data_emissao.strftime('%d/%m/%Y')}")
print(f"Data de Vencimento: {novo_certificado.data_expiracao.strftime('%d/%m/%Y')}")

# Fechamos a sessão ao terminar
sessao.close()