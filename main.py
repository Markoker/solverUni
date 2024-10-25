import re
import networkx as nx
import matplotlib.pyplot as plt

# I need to create a tree from the expression:
# 0.65 * P_cert + 0.1 * P_cont + 0.25 * P_lec
# Where:
# P_cert = (Cert_1 + Cert_2 + Cert_3) / 3
# P_cont = (Cont_1 + Cont_2 + Cont_3) / 3
# P_lec = (Lec_1 + Lec_2 + Lec_3 + Lec_4 + Lec_5) / 5

G = nx.DiGraph()

# Create the nodes
G.add_node("NP")
G.add_node("P_cert")
G.add_node("P_cont")
G.add_node("P_lec")
G.add_node("Cert_1")
G.add_node("Cert_2")
G.add_node("Cert_3")
G.add_node("Cont_1")
G.add_node("Cont_2")
G.add_node("Cont_3")
G.add_node("Lec_1")
G.add_node("Lec_2")
G.add_node("Lec_3")
G.add_node("Lec_4")
G.add_node("Lec_5")

# Create the edges
G.add_edge("NP", "P_cert", weight=0.65)
G.add_edge("NP", "P_cont", weight=0.1)
G.add_edge("NP", "P_lec", weight=0.25)
G.add_edge("P_cert", "Cert_1", weight=1 / 3)
G.add_edge("P_cert", "Cert_2", weight=1 / 3)
G.add_edge("P_cert", "Cert_3", weight=1 / 3)
G.add_edge("P_cont", "Cont_1", weight=1 / 3)
G.add_edge("P_cont", "Cont_2", weight=1 / 3)
G.add_edge("P_cont", "Cont_3", weight=1 / 3)
G.add_edge("P_lec", "Lec_1", weight=1 / 5)
G.add_edge("P_lec", "Lec_2", weight=1 / 5)
G.add_edge("P_lec", "Lec_3", weight=1 / 5)
G.add_edge("P_lec", "Lec_4", weight=1 / 5)
G.add_edge("P_lec", "Lec_5", weight=1 / 5)


# Draw the tree with a tree layout and weight on the edges
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


def generar_LP(G):
    d = {}
    d["NP"] = "root"
    d = rename_nodes("NP", d, "0", G)
    nx.relabel_nodes(G, d, copy=False)

    mod_weights(G, "root", 1)
    c = 1

    LP = "Min: "

    w = []
    main_nodes = []

    for node in G.successors("root"):
        w.append(f"{G["root"][node]['weight']} {node}")
        main_nodes.append(node)
    LP += " + ".join(w) + ";\n"

    LP += "/* Restricción de nota de aprobacion */\n"
    LP += " + ".join(w) + " >= 55;\n\n"

    LP += "/* Restricción de descomposiciones */\n"
    for node in main_nodes:
        LP = decompose_in_children(G, node, LP)
    LP += "\n"

    '''
    Reemplazo de evaluaciones que ya tienen nota.
    '''

    LP += "/* Restricción de positividad y limite de nota */\n"
    for node in G.nodes():
        if node == "root":
            continue

        LP += f"{node} >= 0;\n"
        LP += f"{node} <= 100;\n"

    print(LP)
    with open("out.lp", "w") as f:
        f.write(LP)


generar_LP(G)
