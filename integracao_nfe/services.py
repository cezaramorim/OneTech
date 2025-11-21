# integracao_nfe/services.py
import json
import uuid

def emitir_nfe_api(payload_nfe, certificado_pfx, senha_certificado):
    """
    Função MOCK (simulada) que representa a chamada para uma API externa de emissão de NF-e.
    
    Em um cenário de produção, esta função conteria a lógica real para se comunicar
    com um serviço como eNotas, FocusNFe, etc., usando a biblioteca 'requests'.
    Ela enviaria o payload da nota e os dados do certificado.
    """
    print("--- SIMULANDO CHAMADA PARA API DE EMISSÃO DE NF-e ---")
    print(f"Payload da NFe: {json.dumps(payload_nfe, indent=2, ensure_ascii=False)}")
    print(f"Certificado: {len(certificado_pfx) if certificado_pfx else 0} bytes")
    print(f"Senha do Certificado: {'*' * len(senha_certificado)}")

    # Lógica de simulação de sucesso ou falha
    # Para fins de teste, vamos simular uma falha se o CNPJ do destinatário for "inválido"
    if payload_nfe.get("destinatario", {}).get("cnpj") == "99.999.999/0001-99":
        print("--- SIMULAÇÃO: Falha forçada na API (CNPJ inválido) ---")
        return {
            "success": False,
            "error": "CNPJ do destinatário inválido (simulação de erro da API externa)."
        }
    else:
        print("--- SIMULAÇÃO: Sucesso na API ---")
        # Em um caso real, a resposta viria da API externa.
        return {
            "success": True,
            "id_externo": f"nfe_live_{uuid.uuid4().hex}",
            "status": "processando_autorizacao"
        }
