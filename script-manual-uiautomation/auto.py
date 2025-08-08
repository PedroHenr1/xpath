import uiautomation as auto
import json
import time
from datetime import datetime
import argparse
import win32api


parser = argparse.ArgumentParser()
parser.add_argument('--appname', type=str, help='Nome da janela do aplicativo', required=True)
args = parser.parse_args()
APP_NAME = args.appname

exported_elements = []
checked_elements = set() # para nao repetir elemento no json

# para checar se mouse foi prssionado
def is_left_mouse_pressed():
    return win32api.GetKeyState(0x01) < 0 # 0x01 = código do botão esquerdo do mouse. se for negativo o botão está pressionado.

def get_xpath_path(element):
    try:
        parts = []
        while element and element.ControlTypeName:
            part = f"/{element.ControlTypeName}"
            if element.Name:
                part += f"[@Name='{element.Name}']"
            elif element.AutomationId:
                part += f"[@AutomationId='{element.AutomationId}']"

            parts.insert(0, part)

            element = element.GetParentControl()

        return ''.join(parts)  
    except Exception as e:
        print(f"Erro ao gerar XPath: {e}")
        

def serialize_element(element, depth=0):
    try:
        children_data = []
        
        # vai chamar recursivamente todos os filhos do elemtno clicado
        for child in element.GetChildren():
            children_data.append(serialize_element(child, depth + 1))

        return {
            "Name": element.Name,
            "AutomationId": element.AutomationId,
            "ControlType": element.ControlTypeName,
            "ClassName": element.ClassName,
            "BoundingRectangle": str(element.BoundingRectangle),
            "Path": get_xpath_path(element),
            "Children": children_data
        }
    
    except Exception as e:
        print(f"Erro ao acessar filhos do elemento {element.Name}: {e}")

# essa funcao e usada para verificar se o elemento clicado faz parte do app alvo
def is_ancestor(ancestor, element):
    ancestor_id = ancestor.GetRuntimeId()
    while element:
        # enquanto houver elemento para verificar, sera checado se o id do elemento é o mesmo do ancestral (no caso o app)
        if element.GetRuntimeId() == ancestor_id:
            return True
        # se nao for, pega o pai do elemento atual e continua o loop, ate chegar no ancestral
        element = element.GetParentControl()

    return False # nao achou

def loopExtractorBasendOnFocusAndWindows():
    try:
        window = auto.WindowControl(Name=APP_NAME)
        window.SetActive(); # deixando o app ativo

        if not window.Exists(3):  # Vai tentar procurar por 3 segundos
            raise Exception("App não encontrado. Verificar se está em execução.")

        print("Iniciando processo de extração dos elementos ao clicar")

        last_mouse_state = False
    
        while True:
            # retorna a posição atual do cursor do mouse na tela.
            cursor_pos = auto.GetCursorPos()
            # retorna o elemento em que o mouse esta em cima
            control = auto.ControlFromPoint(*cursor_pos)
            # verifica se o botão esquerdo do mouse está pressionado.
            mouse_pressed = is_left_mouse_pressed()

            # para evitar multiplas capturas enquanto o mouse sendo pressionado
            if mouse_pressed and not last_mouse_state:
                # verifica se o elemnto existe e é filho do app
                if control and is_ancestor(window, control):
                    # pegar o id do elemento para nao duplicar no json
                    rid = str(control.GetRuntimeId())
                    # se nao foi clicado
                    if rid not in checked_elements:
                        # vai puxar as infos
                        checked_elements.add(rid)
                        print(f"Clique detectado em: {control.Name} - {control.ControlTypeName}")
                        exported_elements.append({
                            "clicked_element": serialize_element(control)
                        })

            # atualiza para ver se houve clique, se eu ficar segurnado o botão do mouse, vai ficar sempre true
            last_mouse_state = mouse_pressed

            time.sleep(0.1)

    except KeyboardInterrupt:
        # Salva os dados extraídos no JSON
        with open("ui_tree.json", "w", encoding="utf-8") as f:
            json.dump(exported_elements, f, indent=2, ensure_ascii=False)
        print("Extração concluída e salva como ui_tree.json")
    except Exception as e:
        print(e)

loopExtractorBasendOnFocusAndWindows()
