import os
from bbdd import BBDD

from lp import generar_LP, draw_tree
import networkx as nx
import re
import json
import numpy as np
from scipy.stats import truncnorm
from utils import *
from datetime import datetime


def generar_arbol(formulas):
    pattern_distribucion = re.compile(r"\(([^)]+)\)\s*([/|*])\s*(\d+\.?\d*)")
    pattern_division = re.compile(r"((\d+)\s*(/)\s*(\d+))")
    pattern_division_var = re.compile(r"(({[^}]+})\s*(/)\s*(\d+))")
    pattern_mult_var = re.compile(r"(({[^}]+})\s*(\*)\s*(\d+\.?\d*))")
    pattern_variable_w = re.compile(r"((\d+.?\d*)\s*\*\s*\{([^}]+)\})")

    G = nx.DiGraph()

    for line in formulas:
        line = line[0]
 
        for t in re.findall(pattern_division, line):
            line = re.sub(pattern_division, f"{float(t[1]) / float(t[3])}", line, 1)       

        for t in re.findall(pattern_distribucion, line):
            suma = t[0].split(" + ")
            factor = float(t[2])
            if t[1] == "/":
                factor = 1 / factor
            s = " + ".join([f"{factor} * {s}" for s in suma])
            line = re.sub(pattern_distribucion, s, line, 1)


        for t in re.findall(pattern_division_var, line):
            line = re.sub(pattern_division_var, f"{1 / float(t[3])} * {t[1]}", line, 1)

        for t in re.findall(pattern_mult_var, line):
            line = re.sub(pattern_mult_var, f"{float(t[3])} * {t[1]}", line, 1)

        print(line)
        
        line = line.split(" = ")

        if len(line) != 2:
            raise Exception("Debes tener una igualdad")

        main_var = re.findall(r"{([^}]+)}", line[0])[0]
        var_weights = re.findall(pattern_variable_w, line[1])

        if main_var not in G.nodes:
            G.add_node(main_var)

        for w in var_weights:
            if w[2] not in G.nodes:
                G.add_node(w[2])
            G.add_edge(main_var, w[2], weight=float(w[1]))

    return G


def optimizar_notas(id_asignatura):
    formulas = bbdd.get_formulas(id_asignatura)
    restricciones = bbdd.get_restricciones(id_asignatura)

    G = generar_arbol(formulas)

    print("¿Que nota desea obtener?")
    nota = float(input("Ingrese la nota: "))
    print()

    notas = bbdd.get_evaluaciones(id_asignatura)
    notas = [[nota[0], nota[1], nota[2], nota[3], nota[4]] for nota in notas]

    LP = generar_LP(G, nota, notas, restricciones)
    if LP == -1:
        print("No te quedan evaluaciones sin nota")
        input("Presione enter para continuar")
        return
    elif LP == -2:
        input("Presione enter para continuar")
        return

    supuestos = {}
    evaluaciones_sin_nota = bbdd.get_evaluaciones_sin_nota(id_asignatura)
    while input("¿Analisis de sensibilidad? (y/N): ") == "y":
        evaluaciones_sin_nota = [evaluacion for evaluacion in evaluaciones_sin_nota if evaluacion[2] not in supuestos]

        print("Cambiar una de las notas optimas:")
        for i, evaluacion in enumerate(evaluaciones_sin_nota):
            print(f"{i + 1:>2}: {evaluacion[2]}")
        index = int(input("¿Que nota desea cambiar? ")) - 1
        new_nota = float(input("Ingrese la nueva nota: "))

        index_evaluacion = \
        [i for i, evaluacion in enumerate(notas) if evaluacion[2] == evaluaciones_sin_nota[index][2]][0]

        notas[index_evaluacion][4] = new_nota

        supuestos[evaluaciones_sin_nota[index][2]] = new_nota

        LP = generar_LP(G, nota, notas, restricciones)

        if LP == -1:
            print("No te quedan evaluaciones sin nota")
            input("Presione enter para continuar")
            break
        elif LP == -2:
            input("Presione enter para continuar")
            return
        else:
            for key in supuestos:
                str_nota = colorear(f"{supuestos[key]:.0f}",
                                    color_datos(supuestos[key], [0, 20, 40, 60, 80], reverse=True))
                print(f"{key:<24}{str_nota:>8}")


def actualizar_datos(asignatura_id, alpha=1):
    num_simulaciones = 300000

    formulas = bbdd.get_formulas(asignatura_id)

    G = generar_arbol(formulas)

    base = 0
    pesos = []

    notas = []
    pesos_notas = []

    evaluaciones = bbdd.get_evaluaciones(asignatura_id)
    for evaluacion in evaluaciones:
        eval_name = evaluacion[2]
        w = 1
        actual = eval_name
        while actual != "NP":
            w *= G[list(G.predecessors(actual))[0]][actual]["weight"]
            actual = list(G.predecessors(actual))[0]

        if evaluacion[4] is not None:
            base += w * evaluacion[4]
            notas.append(evaluacion[4])
            pesos_notas.append(w)
        else:
            pesos.append(w)

    all_notas = bbdd.get_notas_evaluaciones()

    mean_all_notas = np.mean(all_notas)

    mean_notas = np.dot(notas, pesos_notas) / np.sum(pesos_notas)
    desv_estandar = np.sqrt(np.dot(pesos_notas, (notas - mean_notas) ** 2) / np.sum(pesos_notas))

    mean_notas_ponderada = alpha * mean_notas + (1 - alpha) * mean_all_notas

    desv_estandar_ponderada = 25

    pesos = np.array(pesos)

    lower, upper = 0, 100  # límites de truncamiento
    a_trunc, b_trunc = (lower - mean_notas_ponderada) / desv_estandar_ponderada, (
                upper - mean_notas_ponderada) / desv_estandar_ponderada
    aprobados = 0
    nota_70 = 0

    for i in range(num_simulaciones):
        printProgressBar(i + 1, num_simulaciones, prefix='Realizando simulaciones:', suffix='Completadas', decimals=2,
                         length=50, printEnd="\r")

        X = truncnorm.rvs(a_trunc, b_trunc, loc=mean_notas_ponderada, scale=desv_estandar_ponderada, size=(len(pesos)))
        NP = base + np.dot(pesos, X)

        if NP >= 55:
            aprobados += 1

        if NP >= 70:
            nota_70 += 1

    bbdd.update_data_asignatura(
        asignatura_id,
        aprobar=aprobados / num_simulaciones,
        nota_70=nota_70 / num_simulaciones,
        media_notas=mean_notas,
        desviacion_notas=desv_estandar,
        nota_minima=base,
        nota_maxima=base + 100 * np.sum(pesos)
    )

def table_asignaturas_pasadas():
    asignaturas = bbdd.get_asignaturas_pasadas()

    headers = ["Asignatura", "Nota"]
    max_lens = [18, 6]
    data = []

    for asignatura in asignaturas:
        nota = asignatura[6]
        c = color_datos(nota, [0, 55, 70])
        nota = colorear(f"{nota:.2f}", c)

        data.append([asignatura[1], f"{nota:^4}"])

    table = Table(headers, data, max_lens)

    print(table)

def table_notas():
    asignaturas = bbdd.get_asignaturas_actuales()
    
    headers = ["Asignatura", "Media", "Nota act", "Nota max", "% Aprobar", "% Nota 70"]
    max_lens = [18, 8, 8, 8, 10, 10]
    data = []

    for asignatura in asignaturas:
        prob_aprobar = asignatura[2]
        prob_70 = asignatura[3]
        media = asignatura[4]
        nota_minima = asignatura[5]
        nota_maxima = asignatura[6]

        if media is None:
            media = "--"
        else:
            media = f"{media:.2f}"

        if nota_minima is None:
            nota_minima = "--"
        else:
            nota_minima = f"{nota_minima:.2f}"

        if nota_maxima is None:
            nota_maxima = "--"
        else:
            nota_maxima = f"{nota_maxima:.2f}"

        if prob_aprobar is None:
            prob_aprobar = "--"
        else:
            c = color_datos(prob_aprobar, [0, 0.2, 0.4, 0.6, 0.8])
            prob_aprobar = colorear(f"{prob_aprobar * 100:.2f}", c)

        if prob_70 is None:
            prob_70 = "--"
        else:
            c = color_datos(prob_70, [0, 0.2, 0.4, 0.6, 0.8])
            prob_70 = colorear(f"{prob_70 * 100:.2f}", c)

        data.append([asignatura[1], media, nota_minima, nota_maxima, prob_aprobar, prob_70])

    table = Table(headers, data, max_lens)
    print(table)


def proximas_evaluaciones():
    evaluaciones = bbdd.get_proximas_evaluaciones()
    if len(evaluaciones) == 0:
        headers = ["No hay evaluaciones próximas"]
        max_lens = [50]
        data = []

        table = Table(headers, data, max_lens)
        print(table)
        return

    headers = ["Asignatura", "Evaluacion", "Fecha", "Dias restantes"]
    max_lens = [18, 30, 30, 16]
    data = []

    for evaluacion in evaluaciones:
        asignatura = bbdd.get_asignatura(evaluacion[1])[1]

        fecha = evaluacion[3]

        if not fecha:
            fecha = "--"
            dias = f'{"--":>15}  '
        else:
            fecha = datetime.strptime(evaluacion[3], "%Y-%m-%d %H:%M:%S") 

            dias = (fecha - datetime.now()).days + 1

            c = color_datos(dias, [1, 5, 10, 20])
            dias = colorear(f"{dias}", c)

            fecha = fecha.strftime("%d/%m/%Y")

        data.append([asignatura, evaluacion[2], fecha, dias])

    table = Table(headers, data, max_lens)
    print(table)

def agregar_asignatura():
    nombre = input("Ingrese el nombre de la asignatura: ")

    formulas = []
    restricciones = []

    opt = 1

    cancel = False

    while opt:
        print("¿Que desea hacer?")
        print("1: Agregar formula")
        print("2: Agregar restricción")
        print("3: Guardar asignatura")
        print("0: Cancelar")

        opt = input("Seleccione una opción: ")

        if opt == "1":
            print("Para agregar una formula, ingrese la expresión matemática en el siguiente formato: \n"
                            "{Variable principal} = <Expresion>\n"
                            "Las expresiones pueden ser de la forma:\n"
                            "  - {Variable} * <Numero decimal separado por .>\n"
                            "  - {Variable} / <Numero decimal separado por .>\n"
                            "  - ({Variable} + {Variable} + ... + {Variable}) * <Numero decimal separado por .>\n"
                            "  - ({Variable} + {Variable} + ... + {Variable}) / <Numero decimal separado por .>\n"
                            "Siempre debe haber una formula cuya variable principal sea NP\n"
                            "Ejemplo:\n"
                            "[Formula 1]: {NP} = {Promedio certamenes} * 0.8 + {Promedio tareas} * 0.2\n"
                            "[Formula 2]: {Promedio certamenes} = {Certamen 1} * 0.3 + {Certamen 2} * 0.3 + {Certamen 3} * 0.4\n"
                            "[Formula 3]: {Promedio tareas} = ({Tarea 1} + {Tarea 2}) / 2\n")
            print("Formulas actuales:")
            print("\n".join(formulas))
            formula = input("Ingresar formula (0 para cancelar): ")


            formulas.append(formula)
        elif opt == "2":
            print("Para agregar una restricción, ingrese la expresión matemática en el siguiente formato: \n"
                    "Las expresiones pueden ser de la forma:\n"
                    "  - {Variable} > <Numero decimal separado por .>\n"
                    "  - {Variable} < <Numero decimal separado por .>\n"
                    "  - {Variable} >= <Numero decimal separado por .>\n"
                    "  - {Variable} <= <Numero decimal separado por .>\n"
                    "Ejemplo:\n"
                    "[Restricción 2]: {Promedio certamenes} > 40\n"
                    "[Restricción 3]: {Promedio tareas} > 50\n"
                    "* No es necesario agregar una restricción para NP\n")
            print("Restricciones actuales:")
            print("\n".join(restricciones))
            restriccion = input("Ingresar restricción (0 para cancelar): ")
            restricciones.append(restriccion)
            continue
        elif opt == "3":
            break
        else:
            cancel = True
            break

    if cancel:
        return

    id_asignatura = bbdd.create_asignatura(nombre)

    try:
        G = generar_arbol([(formula,) for formula in formulas])
        draw_tree(G)
        # Loop through all the leaves of the tree and check if it is in the database
        for node in nx.dfs_postorder_nodes(G):
            if G.out_degree(node) == 0:
                if not bbdd.get_evaluacion_nombre(id_asignatura, node):
                    try:
                        bbdd.create_evaluacion(id_asignatura, node)
                    except:
                        print(f"Error al crear la evaluación {node}")
                        input()
    except:
        print("Hay un error en alguna de las formulas")
        input()
        return

    for formula in formulas:
        bbdd.create_formula(id_asignatura, formula)

    for restriccion in restricciones:
        bbdd.create_restriccion(id_asignatura, restriccion)

    print("\nAsignatura agregada correctamente")
    input("Presione enter para continuar...")



bbdd = BBDD()

menu_asignaturas_actuales = True

def main():
    menu_asignaturas_actuales = True
    while True:
        # Clear the screen
        os.system('clear')

        if menu_asignaturas_actuales:
            table_notas()
            proximas_evaluaciones()

            asignaturas = bbdd.get_asignaturas_actuales()
        else:
            table_asignaturas_pasadas()
            asignaturas = bbdd.get_asignaturas_pasadas()

        print("Opciones:")
        print(" A: Agregar asignatura")

        if menu_asignaturas_actuales:
            print(" C: Cambiar a asignaturas pasadas")
        else:
            print(" C: Cambiar a asignaturas actuales")

        for i, asignatura in enumerate(asignaturas):
            print(f"{i + 1:>2}: Ver {asignatura[1]}")

        op = input("Seleccione una opción: ")
        if op == "A" or op == "a":
            agregar_asignatura()
            continue

        if op == "C" or op == "c":
            menu_asignaturas_actuales = not menu_asignaturas_actuales
            continue
        index_asignatura = int(op)

        if index_asignatura < 1 or index_asignatura > len(asignaturas):
            continue

        index_asignatura -= 1

        asignatura = asignaturas[index_asignatura]

        opcion = 1 

        while opcion != "0":
            # Clear the screen
            os.system('clear')
            print(f"Asignatura: {asignatura[1]}")
            print()
            print("¿Qué desea hacer?")
            print("1: Optimizar notas")
            print("2: Modificar")
            print("3: Ver notas")
            print("4: Ver formula de NP")
            print("5: Ver restricciones")
            print()
            print("0: Cambiar de asignatura")

            opcion = input("Seleccione una opción: ")
            os.system('clear')

            if opcion == "1":
                print(f"Optimizando notas de {asignatura[1]}\n") 
                optimizar_notas(asignatura[0])
            elif opcion == "2":
                print(f"Modificar {asignatura[1]}\n")
                evaluaciones = bbdd.get_evaluaciones(asignatura[0])

                print("Evaluaciones:")
                print(f"{' ':>2}  {'Evaluacion':<32} {'Nota':>4} {'Fecha':^12}")
                for i, evaluacion in enumerate(evaluaciones):
                    fecha = evaluacion[3]
                    if fecha:
                        fecha = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
                    else:
                        fecha = "--"

                    nota = evaluacion[4]
                    if nota is not None:
                        c = color_datos(nota, [0, 20, 40, 60, 80])
                        nota = colorear(f"{int(nota):>4}", c)
                    else:
                        nota = f"{'--':^4}"

                    print(f"{i + 1:>2}: {evaluacion[2]:<32} {nota} {fecha:^12}")

                index = int(input("¿Que evaluacion desea modificar? ")) - 1

                print("¿Que desea hacer?")
                print("1: Cambiar fecha")
                print("2: Cambiar nota")
                print("0: Cancelar")
                
                eval_opcion = input("Seleccione una opción: ")

                if eval_opcion == "1":
                    new_fecha = input("Ingrese la nueva fecha (dd/mm/yyyy): ")
                    new_fecha = datetime.strptime(new_fecha, "%d/%m/%Y")
                    bbdd.update_fecha_evaluacion(evaluaciones[index][0], new_fecha)
                elif eval_opcion == "2":
                    new_nota = float(input("Ingrese la nueva nota: "))
                    bbdd.update_valor_evaluacion(evaluaciones[index][0], new_nota)

                    actualizar_datos(asignatura[0])
            elif opcion == "3":
                print(f"Notas de {asignatura[1]}\n")
                evaluaciones = bbdd.get_evaluaciones_rango_nota(asignatura[0], 0, 1000)

                print(f"{' ':>2}  {'Evaluacion':<32} {'Nota':>4}")
                for i, evaluacion in enumerate(evaluaciones):
                    nota = evaluacion[4]
                    c = color_datos(nota, [0, 20, 40, 60, 80])
                    nota = colorear(f"{nota}", c)

                    print(f"{i+1:>2}: {evaluacion[2]:<32} {nota:>4}")
                input("Presione enter para continuar...")
            elif opcion == "4":
                print(f"Formula de {asignatura[1]}\n")
                formulas = bbdd.get_all_formulas(asignatura[0])
                
                for i, formula in enumerate(formulas):
                    print(f"{i + 1:>2}: {formula[2]}")

                print()
                print("{len(formulas) + 1:>2}: Agregar formula")
                print("{len(formulas) + 2:>2}: Ver arbol")
                print("0: Salir")

                opcion_formula = input("Seleccione una formula: ")

                if opcion_formula == str(len(formulas) + 1):
                    continue

                if opcion_formula == str(len(formulas) + 2):
                    try:
                        G = generar_arbol([(formula[2],) for formula in formulas])
                        draw_tree(G)
                    except:
                        print("Hay un error en alguna de las formulas")
                        input()
                        continue
                    continue

                try:
                    opcion_formula = int(opcion_formula)
                except:
                    continue

                if opcion_formula < 1 and opcion_formula > len(formulas):
                    continue

                print("¿Que desea hacer?")
                print("1: Modificar")
                print("2: Borrar")
                print("0: Cancelar")

                operacion = input("Seleccione una opción: ")

                if operacion == "1":
                    print("Evaluaciones actuales:")
                    evaluaciones = bbdd.get_evaluaciones(asignatura[0])
                    for i, evaluacion in enumerate(evaluaciones):
                        print(f"{i + 1:>2}: {evaluacion[2]}")
                    print()
                    nueva_formula = input("Ingrese la nueva formula: ")
                    
                    
                    new_formulas = [(formula[2],) for formula in formulas]
                    new_formulas[opcion_formula - 1] = (nueva_formula,)
                    
                    try:
                        G = generar_arbol(new_formulas)
                        draw_tree(G) 
                    except Exception as e:
                        print("Error: ")
                        print(e)
                        input()
                        continue

                    # Loop through all the leaves of the tree and check if it is in the database
                    for node in nx.dfs_postorder_nodes(G):
                        if G.out_degree(node) == 0:
                            if not bbdd.get_evaluacion_nombre(asignatura[0], node):
                                try:
                                    bbdd.create_evaluacion(asignatura[0], node)
                                except:
                                    print(f"Error al crear la evaluación {node}")
                                    input()

                    try:
                        bbdd.update_expresion_formula(formulas[opcion_formula - 1][0], nueva_formula)
                    except:
                        print("Error al actualizar la formula")
                        input()
                elif operacion == "2":
                    bbdd.delete_formula(formulas[opcion_formula - 1][0])
            elif opcion == "5":
                continue
                print(f"Restricciones de {asignatura[1]}\n")
                formulas = bbdd.get_all_restricciones(asignatura[0])
                
                for i, formula in enumerate(formulas):
                    print(f"{i + 1:>2}: {formula[2]}")

                print()
                print("0: Salir")

                opcion_formula = input("Seleccione una restricción: ")

                try:
                    opcion_formula = int(opcion_formula)
                except:
                    continue

                if opcion_formula < 1 and opcion_formula > len(formulas):
                    continue

                print("¿Que desea hacer?")
                print("1: Modificar")
                print("2: Borrar")
                print("0: Cancelar")

                operacion = input("Seleccione una opción: ")

                if operacion == "1":
                    nueva_formula = input("Ingrese la nueva restricción: ")
                    bbdd.update_expresion_formula(formulas[opcion_formula - 1][0], nueva_formula)
                elif operacion == "2":
                    bbdd.delete_formula(formulas[opcion_formula - 1][0])
            else:
                break


main()
