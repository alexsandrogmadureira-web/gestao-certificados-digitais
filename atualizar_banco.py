from datetime import timedelta
from sqlalchemy.orm import sessionmaker
from database import engine, Certificado

# Conecta ao banco de dados PostgreSQL
Session = sessionmaker(bind=engine)
sessao = Session()

# Busca todos os certificados existentes no banco
certificados = sessao.query(Certificado).all()

print(f"Encontrados {len(certificados)} certificados. Recalculando validade para 2 anos...")

for cert in certificados:
    # Recalcula a expiração: Data de Emissão + 2 anos (730 dias)
    nueva_expiracao = cert.data_emissao + timedelta(days=730)
    cert.data_expiracao = nueva_expiracao

# Salva as alterações no PostgreSQL
sessao.commit()
sessao.close()

print("✅ Todos os certificados foram atualizados com sucesso para a validade de 2 anos!")