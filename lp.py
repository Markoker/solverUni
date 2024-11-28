import re
import networkx as nx
import matplotlib.pyplot as plt
import os
from utils import color_datos, colorear

def draw_tree(G):
    nx.draw(G,
            with_labels=True,
            pos=nx.nx_agraph.graphviz_layout(G, prog='dot'),
            node_size=1000,
            node_color='green',
            font_size=10,
            font_color='white',
            edge_color='black',
            width=1)
    nx.draw_networkx_edge_labels(G,
                                 pos=nx.nx_agraph.graphviz_layout(G, prog='dot'),
                                 edge_labels={(u, v): d['weight'] for u, v, d in G.edges(data=True)})
    plt.show()


def rename_nodes(origin, d, s, G):
    t = 0
    for node in G.successors(origin):
        d[node] = f"x{s}{t}"
        d = rename_nodes(node, d, s + str(t), G)
        t += 1

    return d


def mod_weights(G, origin, weight):
    # As G is a DiGraph, I need to iterate over the nodes that are right descendants of the origin node
    for node in G.successors(origin):
        G[origin][node]['weight'] *= weight
        mod_weights(G, node, G[origin][node]['weight'])


def decompose_in_children(G, origin, LP):
    if len(list(G.successors(origin))) == 0:
        return LP

    w = []
    for node in G.successors(origin):
        w.append(f"{G[origin][node]['weight']} {node}")
    LP += " + ".join(w) + f" = {origin};\n"

    for node in G.successors(origin):
        LP = decompose_in_children(G, node, LP)

    return LP


def generar_LP(main_G, nota_deseada, evaluaciones, restricciones=None):
    if restricciones is None:
        restricciones = []

    G = main_G.copy()

    d = {"NP": "root"}
    d = rename_nodes("NP", d, "0", G)
    nx.relabel_nodes(G, d, copy=False)

    evaluaciones_con_nota = []
    evaluaciones_sin_nota = []
    
    for evaluacion in evaluaciones:
        if evaluacion[4] is None:
            evaluaciones_sin_nota.append(evaluacion)
        else:
            evaluaciones_con_nota.append(evaluacion)

    if len(evaluaciones_sin_nota) == 0:
        return -1

    delta = 15 * len(evaluaciones_sin_nota) / len(evaluaciones)

    w = []
    for node in G.successors("root"):
        w.append(f"{(G['root'][node]['weight'] ** 2)} {node}")
    LP = f"Min: {' + '.join(w)};\n"

    w = []
    main_nodes = []

    for node in G.successors("root"):
        w.append(f"{G["root"][node]['weight']} {node}")
        main_nodes.append(node)

    LP += "\n/* Restricción de nota de aprobacion */\n"
    LP += " + ".join(w) + f" >= {nota_deseada};\n"

    LP += "\n/* Restricciones base */\n"
    for restriccion in restricciones:
        restriccion = restriccion[0]
        pat = re.findall(r"({([^}]+)})", restriccion)
        if len(pat) == 0:
            continue
        for p in pat:
            restriccion = restriccion.replace(p[0], d[p[1]])
        LP += f"{restriccion};\n"

    LP += "\n/* Restricción de descomposiciones */\n"
    for node in main_nodes:
        LP = decompose_in_children(G, node, LP)

    LP += "\n/* Reemplazo de evaluaciones con nota */\n"
    for evaluacion in evaluaciones_con_nota:
        LP += f"{d[evaluacion[2]]} = {evaluacion[4]};\n"

    LP += "\n/* Restriccion de balance */\n"
    for i in range(len(evaluaciones_sin_nota)):
        for j in range(len(evaluaciones_sin_nota)):
            if i == j:
                continue
            LP += f"{d[evaluaciones_sin_nota[i][2]]} - {d[evaluaciones_sin_nota[j][2]]} <= {delta};\n"

    LP += "\n/* Restricción de positividad y limite de nota */\n"
    for node in G.nodes():
        if node == "root":
            continue

        LP += f"{node} >= 0;\n"

    LP += "\n/* Restricción de limite de nota */\n"
    for evaluacion in evaluaciones_sin_nota:
        LP += f"{d[evaluacion[2]]} <= 100;\n"

    with open("out.lp", "w") as f:
        f.write(LP)

    solve = "lp_solve out.lp > out.txt"
    os.system(solve)

    with open("out.txt", "r") as f:
        text = f.read()

        if "infeasible" in text:
            print("No se puede alcanzar la nota deseada")
            return -2
        pattern = r'(x\d+)\ +(\d+\.?\d+)'
        matches = re.findall(pattern, text)

        d = {v: k for k, v in d.items()}

        print(f"Para obtener una nota de {nota_deseada} se deben obtener las siguientes notas:")
        for match in matches:
            flag = True
            eval_name = ""
            for evaluacion in evaluaciones:
                eval_name = evaluacion[2]

                if d[match[0]] == eval_name:
                    flag = False

                    if evaluacion[4] is not None:
                        flag = True
                        break

            if flag:
                continue

            nota = round(float(match[1])) 
            
            nota = colorear(nota, color_datos(nota, [0, 20, 40, 60, 80], reverse=True))

            print(f"{d[match[0]]:<24}{nota:>8}")
