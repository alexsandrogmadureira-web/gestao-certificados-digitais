import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from database import engine, Colaborador, Certificado

# Configuração da página
st.set_page_config(page_title="Gestão de Certificados Digitais", layout="wide")

# Inicializa a sessão do Banco de Dados
Session = sessionmaker(bind=engine)
sessao = Session()

# Menu Lateral
st.sidebar.title("🏥 Menu do Sistema")
opcao_menu = st.sidebar.radio("Navegação", ["Dashboard (Vencimentos)", "Novo Cadastro", "Ocorrências (Perdas/Roubos)"])

# --- PÁGINA 1: DASHBOARD ---
if opcao_menu == "Dashboard (Vencimentos)":
    st.title("📊 Painel de Vencimentos")

    # Campo de Busca
    termo_busca = st.text_input("🔍 Buscar por Nome ou CPF", "")

    certificados = sessao.query(Certificado).all()
    dados = []
    hoje = datetime.now()
    certificados_pendentes = {}

    for cert in certificados:
        colab = sessao.query(Colaborador).filter_by(id=cert.colaborador_id).first()

        # Filtro da Busca
        if termo_busca and termo_busca.upper() not in colab.nome_completo and termo_busca not in colab.cpf:
            continue

        dias_restantes = (cert.data_expiracao - hoje).days

        if dias_restantes < 0:
            status = "🔴 Vencido"
        elif dias_restantes <= 30:
            status = "🟠 Vence em 30 dias"
        elif dias_restantes <= 60:
            status = "🟡 Vence em 60 dias"
        elif dias_restantes <= 90:
            status = "🔵 Vence em 90 dias"
        else:
            status = "🟢 Regular"

        dados.append({
            "Nome": colab.nome_completo,
            "CPF": colab.cpf,
            "Função": colab.funcao,
            "Tipo": cert.tipo_certificado,
            "Status Entrega": cert.status_entrega,
            "Vencimento": cert.data_expiracao.strftime('%d/%m/%Y'),
            "Dias Restantes": dias_restantes,
            "Status": status
        })

        if cert.status_entrega == "Pendente":
            certificados_pendentes[f"{colab.nome_completo} - CPF: {colab.cpf} ({cert.tipo_certificado})"] = cert.id

    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum certificado encontrado.")

    # Ferramenta rápida para registrar a entrega do Token
    if certificados_pendentes:
        st.markdown("---")
        st.subheader("📦 Registrar Entrega de Token / Certificado")
        with st.form("form_entrega", clear_on_submit=True):
            cert_selecionado = st.selectbox("Selecione o Colaborador que veio buscar:",
                                            options=list(certificados_pendentes.keys()))
            data_entrega_real = st.date_input("Data da Entrega", datetime.today(), format="DD/MM/YYYY")
            btn_entregar = st.form_submit_button("Confirmar Entrega")

            if btn_entregar:
                cert_id = certificados_pendentes[cert_selecionado]
                cert_bd = sessao.query(Certificado).filter_by(id=cert_id).first()

                cert_bd.data_entrega = datetime.combine(data_entrega_real, datetime.min.time())
                cert_bd.status_entrega = "Entregue"
                sessao.commit()
                st.success("Entrega registrada com sucesso! Pressione F5 para atualizar a tabela.")

# --- PÁGINA 2: NOVO CADASTRO ---
elif opcao_menu == "Novo Cadastro":
    st.title("➕ Cadastrar Novo Certificado")

    with st.form("form_cadastro", clear_on_submit=True):
        st.subheader("Dados do Colaborador")
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome Completo")
        cpf = col2.text_input("CPF")
        funcao = st.text_input("Função (Ex: Médico, Enfermeiro)")

        st.subheader("Dados do Certificado")
        col3, col4 = st.columns(2)
        tipo = col3.selectbox("Tipo de Certificado", ["A3", "A1"])
        modalidade = col4.selectbox("Modalidade de Emissão", ["Presencial", "Videoconferência"])

        # Mostra o campo de Serial apenas se for A3
        patrimonio_token = None
        if tipo == "A3":
            col_serial, col_vazia = st.columns(2)
            patrimonio_token = col_serial.text_input("Número de Série do Token A3 (Opcional)")

        # Datas lado a lado no formato brasileiro (Fora da regra do A3)
        col5, col6 = st.columns(2)
        data_emissao = col5.date_input("Data de Emissão", datetime.today(), format="DD/MM/YYYY")
        data_entrega = col6.date_input("Data de Entrega", value=None, format="DD/MM/YYYY")

        st.write("")
        entregue = st.checkbox("Confirmar que o certificado foi entregue ao colaborador nesta data?")

        submit = st.form_submit_button("Salvar Cadastro")

        if submit:
            if nome and cpf:
                # Tratamento de Dados
                nome_tratado = nome.upper()
                cpf_limpo = "".join(filter(str.isdigit, cpf))
                if len(cpf_limpo) == 11:
                    cpf_tratado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
                else:
                    cpf_tratado = cpf

                # Salva Colaborador
                novo_colab = Colaborador(nome_completo=nome_tratado, cpf=cpf_tratado, funcao=funcao)
                sessao.add(novo_colab)
                sessao.commit()

                data_expiracao = data_emissao + timedelta(days=1095)

                # Trata os dados de entrega baseados no checkbox e se a data foi preenchida
                if entregue and data_entrega is not None:
                    data_entrega_bd = datetime.combine(data_entrega, datetime.min.time())
                    status_entrega_bd = "Entregue"
                else:
                    data_entrega_bd = None
                    status_entrega_bd = "Pendente"

                # Salva o Certificado
                novo_cert = Certificado(
                    colaborador_id=novo_colab.id,
                    tipo_certificado=tipo,
                    modalidade_emissao=modalidade,
                    data_emissao=datetime.combine(data_emissao, datetime.min.time()),
                    data_expiracao=datetime.combine(data_expiracao, datetime.min.time()),
                    data_entrega=data_entrega_bd,
                    status_entrega=status_entrega_bd,
                    patrimonio_token=patrimonio_token
                )
                sessao.add(novo_cert)
                sessao.commit()

                st.success(f"Certificado de {nome_tratado} salvo com sucesso! Validade automática: {data_expiracao.strftime('%d/%m/%Y')}")

                if status_entrega_bd == "Pendente":
                    st.info("📌 O certificado foi salvo, mas o status de entrega ficou como PENDENTE pois a caixa não foi marcada.")
                else:
                    st.info("✅ Certificado salvo e marcado como ENTREGUE.")
            else:
                st.error("Por favor, preencha o Nome e o CPF.")

# --- PÁGINA 3: OCORRÊNCIAS ---
elif opcao_menu == "Ocorrências (Perdas/Roubos)":
    st.title("⚠️ Registro de Ocorrências")
    st.write("Registre perdas, roubos ou danos de tokens/certificados para revogação e solicitação de 2ª via.")

    # 1. Busca todos os certificados já cadastrados
    certificados = sessao.query(Certificado).all()

    if not certificados:
        st.warning("Nenhum certificado cadastrado no sistema ainda. Cadastre um certificado primeiro.")
    else:
        # Cria uma lista bonita com Nome e CPF para o usuário escolher no menu suspenso
        opcoes_certs = {}
        for cert in certificados:
            colab = sessao.query(Colaborador).filter_by(id=cert.colaborador_id).first()
            label = f"{colab.nome_completo} - CPF: {colab.cpf} (Tipo: {cert.tipo_certificado})"
            opcoes_certs[label] = cert.id  # Guarda o ID do certificado escondido

        # Selectbox para escolher o colaborador
        certificado_selecionado = st.selectbox("Selecione o Colaborador / Certificado:",
                                               options=list(opcoes_certs.keys()))

        # Pega o ID real do certificado baseado na escolha
        cert_id = opcoes_certs[certificado_selecionado]

        # 2. Formulário da Ocorrência
        with st.form("form_ocorrencia", clear_on_submit=True):
            col1, col2 = st.columns(2)

            tipo_ocorrencia = col1.selectbox("Tipo de Ocorrência",
                                             ["Perda", "Roubo", "Dano Físico (Token Quebrado)", "Esquecimento de Senha",
                                              "Outro"])
            data_ocorrencia = col2.date_input("Data do Ocorrido", datetime.today(), format="DD/MM/YYYY")

            st.write("")
            necessita_segunda_via = st.checkbox("Colaborador necessita de 2ª via (Nova Emissão)?", value=True)

            observacoes = st.text_area("Observações Adicionais", placeholder="Ex: Boletim de Ocorrência nº 12345...")

            # NOVO: Campo para anexar o documento
            arquivo_anexo = st.file_uploader("Anexar Documento (PDF, JPG, PNG)", type=["pdf", "jpg", "jpeg", "png"])

            submit_ocorrencia = st.form_submit_button("Registrar Ocorrência")

            if submit_ocorrencia:
                caminho_salvo = None

                # Lógica para salvar o arquivo na máquina/servidor
                if arquivo_anexo is not None:
                    # Cria a pasta 'anexos' no seu projeto, se ela não existir
                    os.makedirs("anexos", exist_ok=True)

                    # Define onde o arquivo será salvo
                    caminho_salvo = os.path.join("anexos", arquivo_anexo.name)

                    # Salva o arquivo fisicamente
                    with open(caminho_salvo, "wb") as f:
                        f.write(arquivo_anexo.getbuffer())

                # Salva a ocorrência no banco de dados
                nova_ocorrencia = Ocorrencia(
                    certificado_id=cert_id,
                    tipo_ocorrencia=tipo_ocorrencia,
                    data_ocorrencia=datetime.combine(data_ocorrencia, datetime.min.time()),
                    status_revogacao="Pendente",
                    necessita_segunda_via=necessita_segunda_via,
                    observacoes=observacoes,
                    caminho_anexo=caminho_salvo  # Salva apenas o local do arquivo
                )

                sessao.add(nova_ocorrencia)
                sessao.commit()

                st.success("Ocorrência registrada com sucesso!")

                if arquivo_anexo is not None:
                    st.info(f"📁 Documento '{arquivo_anexo.name}' salvo na pasta de anexos.")

                if necessita_segunda_via:
                    st.warning("🚨 O colaborador foi marcado para emissão de 2ª via.")

# Fechando a sessão do banco
sessao.close()