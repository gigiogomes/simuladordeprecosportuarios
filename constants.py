# constants.py

# Tamanhos de Contêineres
TAMANHO_20 = "20'"
TAMANHO_40 = "40'"
TAMANHOS_PERMITIDOS = [TAMANHO_20, TAMANHO_40]

# Tipos de Contêineres
TIPO_DRY = "Dry"
TIPO_REEFER = "Reefer"

# Características Especiais
CARAC_IMO = "IMO (Perigosa)"
CARAC_OOG = "OOG (Excesso)"
CARAC_ANUENCIA = "Anuência"

# Gatilhos do Sistema
GATILHO_NENHUM = "Nenhum"
GATILHO_REEFER = "Contêiner Reefer"
GATILHO_IMO = "Carga IMO (Perigosa)"
GATILHO_OOG = "Carga OOG (Excesso)"
GATILHO_ANUENCIA = "Anuência (MAPA/ANVISA)"
OPCOES_GATILHO = [GATILHO_NENHUM, GATILHO_REEFER, GATILHO_IMO, GATILHO_OOG, GATILHO_ANUENCIA]