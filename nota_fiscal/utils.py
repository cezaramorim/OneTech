# nota_fiscal/utils.py
import xml.etree.ElementTree as ET


def element_to_dict(elem):
    """
    Converte recursivamente um ElementTree.Element em dict,
    incluindo atributos, texto e filhos.
    """
    node = {}
    # inclui atributos se existirem
    if elem.attrib:
        node.update(elem.attrib)

    # processa filhos
    for child in elem:
        child_dict = element_to_dict(child)
        tag = child.tag
        if tag in node:
            # se já existe, transforma em lista
            if not isinstance(node[tag], list):
                node[tag] = [node[tag]]
            node[tag].append(child_dict)
        else:
            node[tag] = child_dict

    # inclui texto se for relevante
    text = (elem.text or '').strip()
    if text:
        # se não há outros dados, retorna só o texto
        if not node:
            return text
        node['#text'] = text

    return node


def importar_nfe_e_retornar_json(xml_file):
    """
    Lê o XML da NFe e retorna um dict completo com toda a árvore de elementos.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # Converte a raiz inteira em dict
    return element_to_dict(root)
