import uiautomation as auto
import json
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('--appname', type=str, help='Calculator')

args = parser.parse_args()

# essa funcao vai verificar os elementos da aplicação e os filhos desses elementos
def serialize_element(element, depth=0):
    children_data = []
    for child in element.GetChildren(): # para cada filho, ele vai chamar esse metodo de novo, a ideia é pegar os filhos dos filhos
        children_data.append(serialize_element(child, depth + 1))

    data = {
        "Name": element.Name, # cada elemento vai ter esses dados aqui
        "AutomationId": element.AutomationId,
        "ControlType": element.ControlTypeName,
        "ClassName": element.ClassName,
        "BoundingRectangle": str(element.BoundingRectangle),
        "Path": get_xpath_path(element),
        "Children": children_data # com info dos filhos
    }
    return data

def get_xpath_path(element):
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

def find_all_controls(root, condition):
    results = []

    def walk(element):
        if condition(element):
            results.append(element)
        for child in element.GetChildren():
            walk(child)

    walk(root)
    return results


# Expande aba
def extract_by_tabs(window):
    resp = []

    tabs = find_all_controls(
        window,
        lambda c: c.ControlTypeName in ['ListItemControl'] 
    )

    print(tabs)

    if not tabs:
        full_tree = serialize_element(window)
        resp.append({
            "Tree": full_tree
        })
        return resp

    for tab in tabs:
        try:
            print(f"{tab.Name} - {tab.ControlTypeName}")
            tab.Click()
            time.sleep(1)
            tree = serialize_element(window)
            resp.append({
                "ExpandedTab": tab.Name,
                "Tree": tree
            })
            tab.Click() # para fechar uma aba tem que clicar de novo
        except Exception as e:
            print(e)

    return resp


window = auto.WindowControl(Name="Calculator")
window.SetActive()

if window.Exists(3): 
    # print(dir(window)) # para saber quais pametos pegar
    print(f"Extraindo XPath do aplicativo '{args.appname}'")
    res = extract_by_tabs(window)

    with open("ui_tree.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print("Extração concluída e salva como ui_tree.json")
else:
    print("Janela não encontrada.")