from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timedelta

# Aqui definimos que vamos usar SQLite para testar localmente no PyCharm.
# Futuramente, no Docker, mudaremos apenas esta linha para o PostgreSQL.
#URL_BANCO_DADOS = "sqlite:///certificados_hospital.db"
URL_BANCO_DADOS = "postgresql+psycopg2://admin:senha_hospital@192.168.140.90:5432/certificados_db"

engine = create_engine(URL_BANCO_DADOS, echo=True)  # echo=True mostra o SQL no terminal
Base = declarative_base()


# --- TABELA 1: COLABORADORES ---
class Colaborador(Base):
    __tablename__ = 'colaboradores'

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String, nullable=False)
    cpf = Column(String, unique=True, index=True, nullable=False)
    funcao = Column(String)
    conselho_numero = Column(String)  # CRM, COREN, etc.
    #setor = Column(String)
    status_ativo = Column(Boolean, default=True)

    # Isso cria uma ligação para podermos ver todos os certificados de um colaborador
    certificados = relationship("Certificado", back_populates="colaborador")


# --- TABELA 2: CERTIFICADOS ---
class Certificado(Base):
    __tablename__ = 'certificados'

    id = Column(Integer, primary_key=True, index=True)
    colaborador_id = Column(Integer, ForeignKey('colaboradores.id'))

    tipo_certificado = Column(String)  # 'A1' ou 'A3'
    modalidade_emissao = Column(String)  # 'Fisica' ou 'Video'

    data_emissao = Column(DateTime, nullable=False)
    data_expiracao = Column(DateTime, nullable=False)
    data_entrega = Column(DateTime, nullable=True)  # Pode estar vazio até a pessoa buscar
    status_entrega = Column(String, default="Pendente")  # 'Pendente', 'Entregue'
    patrimonio_token = Column(String, nullable=True)  # Número de série do Token A3

    # Ligações
    colaborador = relationship("Colaborador", back_populates="certificados")
    ocorrencias = relationship("Ocorrencia", back_populates="certificado")


# --- TABELA 3: OCORRÊNCIAS (Perdas, Roubos, etc) ---
class Ocorrencia(Base):
    __tablename__ = 'ocorrencias'

    id = Column(Integer, primary_key=True, index=True)
    certificado_id = Column(Integer, ForeignKey('certificados.id'))

    tipo_ocorrencia = Column(String)
    data_ocorrencia = Column(DateTime, default=datetime.utcnow)
    status_revogacao = Column(String, default="Pendente")
    necessita_segunda_via = Column(Boolean, default=True)
    observacoes = Column(String)
    caminho_anexo = Column(String, nullable=True)  # NOVA COLUNA AQUI

    certificado = relationship("Certificado", back_populates="ocorrencias")


# --- COMANDO PARA CRIAR O BANCO DE DADOS ---
# Se você rodar este arquivo diretamente, ele vai criar o arquivo .db com as tabelas.
if __name__ == "__main__":
    print("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Banco de dados criado com sucesso!")