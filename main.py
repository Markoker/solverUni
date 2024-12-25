import datetime
import json

from db.db import db
from table import Table
from config import config
import os
import re
from curso import Curso

DB = db()


def mostrar_estado_cursos():
    cursos = DB.get_cursos(query_type="no_finalizados")

    print("\n--- Estado de Cursos ---")
    if not cursos:
        print("No tienes cursos registrados.")
    else:
        headers = ["Curso", "Nota Actual", "Probabilidad de Aprobar"]
        data = [[curso['nombre'], curso['nota'], f"{curso['prob_aprobar']:.2f}%"] for curso in cursos]
        max_lens = [20, 15, 25]  # Ajusta los tamaños según sea necesario
        table = Table(headers=headers, data=data, max_lens=max_lens)
        print(table)


def mostrar_tareas_hoy():
    tareas = DB.obtener_tareas_hoy()
    hoy = datetime.date.today().strftime("%Y-%m-%d")
    print("\n--- Tareas para Hoy ---")
    if not tareas:
        print("No tienes tareas para hoy.")
    else:
        headers = ["ID", "Tarea", "Curso", "Completada"]
        data = [[tarea['id'], tarea['nombre'], tarea['curso'], tarea["completada"]] for tarea in tareas]
        max_lens = [25, 20, 10]  # Ajusta los tamaños según sea necesario
        table = Table(headers=headers, data=data, max_lens=max_lens)
        print(table)


def modificar_evaluaciones(curso_id):
    opcion = None
    while opcion != "5":
        os.system('clear')
        curso = DB.get_curso(curso_id)

        print(f"\n--- Modificar Evaluaciones {curso['nombre']} ---")

        evaluaciones = DB.obtener_evaluaciones_curso(curso_id)
        if evaluaciones:
            headers = ["ID", "Evaluación", "Nota", "Mínimo", "Máximo", "Fecha"]
            data = [[eva['id'], eva['nombre'], eva['nota'], eva['min'], eva['max'], eva['fecha']] for eva in
                    evaluaciones]
            max_lens = [5, 20, 10, 10, 10, 15]
            table = Table(headers=headers, data=data, max_lens=max_lens)
            print(table)

        opcion = input(
            f"\n1. Modificar nota evaluación\n2. Modificar fecha evaluación\n3. Agregar evaluación\n4. Eliminar evaluación\n5. Volver\n\nElige una opción: ")

        cfg = config()
        nota_min = cfg.get_nota_minima()
        nota_max = cfg.get_nota_maxima()

        if opcion == "3":
            try:
                nombre = input("\nIngresa el nombre de la evaluación (Reemplazar numero por [:n] para crear rango): ")

                minimo = input(f"Ingresa la nota mínima [Default: {nota_min}]: ")
                if not minimo:
                    minimo = nota_min
                else:
                    minimo = float(minimo)

                maximo = input(f"Ingresa la nota máxima [Default: {nota_max}]: ")
                if not maximo:
                    maximo = nota_max
                else:
                    maximo = float(maximo)

                if minimo > maximo:
                    print("La nota mínima no puede ser mayor a la nota máxima.")
                    input("\nPresiona Enter para continuar...")
                    continue

                # Revisar si el nombre tiene un rango de numeros
                if re.search(r"\[:\d+\]", nombre):
                    n = int(re.findall(r"\[:(\d+)\]", nombre)[0])

                    for i in range(n):
                        DB.insert_evaluacion(curso_id, nombre.replace(f"[:{n}]", str(i + 1)), minimo, maximo, None)
                    print("Evaluaciones agregadas exitosamente.")
                    continue

                fecha = input("Ingresa la fecha (YYYY-MM-DD) [Enter para dejar vacío]: ")
                if not fecha:
                    fecha = None
                else:
                    fecha = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()

                DB.insert_evaluacion(curso_id, nombre, minimo, maximo, fecha)
                print("Evaluación agregada exitosamente.")
            except ValueError:
                print("Error en los datos ingresados. Intenta nuevamente.")
                input("\nPresiona Enter para continuar...")
        elif opcion == "1":
            if not evaluaciones:
                print("No hay evaluaciones registradas para este curso.")
                input("\nPresiona Enter para continuar...")
                return
            try:
                eva_id = int(input("\nIngresa el ID de la evaluación: "))
                nota = float(input("Ingresa la nueva nota: "))
                DB.modificar_nota_evaluacion(eva_id, nota)
                print("Nota modificada exitosamente.")
            except ValueError:
                print("ID o nota no válidos. Inténtalo de nuevo.")
                input("\nPresiona Enter para continuar...")
        elif opcion == "2":
            if not evaluaciones:
                print("No hay evaluaciones registradas para este curso.")
                input("\nPresiona Enter para continuar...")
                return
            try:
                eva_id = int(input("\nIngresa el ID de la evaluación: "))
                fecha = input("Ingresa la nueva fecha (YYYY-MM-DD): ")
                fecha = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
                DB.modificar_fecha_evaluacion(eva_id, fecha)
                print("Fecha modificada exitosamente.")
            except ValueError:
                print("ID o fecha no válidos. Inténtalo de nuevo.")
                input("\nPresiona Enter para continuar...")
        elif opcion == "4":
            if not evaluaciones:
                print("No hay evaluaciones registradas para este curso.")
                input("\nPresiona Enter para continuar...")
                return
            try:
                eva_id = int(input("\nIngresa el ID de la evaluación a eliminar: "))
                DB.eliminar_evaluacion(eva_id)
                print("Evaluación eliminada exitosamente.")
            except ValueError:
                print("ID no válido. Inténtalo de nuevo.")
                input("\nPresiona Enter para continuar...")
        else:
            return


def agregar_formula(curso_id, evals, var=None, formula_id=None):
    while True:
        try:
            formula = input(f"Ingresa la fórmula [h para ayuda]: {'{' + var + '}'} = ")
            while formula == "h":
                print("Formato: {Nombre variable} = {<nombre_evaluación>} + {<nombre_evaluación>} * 0.5")
                print("Suma por rango: {Certamen [+1:3]} => ({Certamen 1} + {Certamen 2} + {Certamen 3})")
                print("Producto por rango: {Certamen [*1:3]} => ({Certamen 1} * {Certamen 2} * {Certamen 3})")
                formula = input(f"Ingresa la fórmula [h para ayuda]: {'{' + var + '}'} = ")

            vars_formula = re.findall(r"\{([^\}]*)\}", formula)
            vars_formula = list(dict.fromkeys(vars_formula))

            for var_f in vars_formula:
                rango = re.findall(r"(.*)\[(\+|\*)(\d+):(\d+)\](.*)", var_f)

                if not rango:
                    continue

                l = []
                for i in range(int(rango[0][2]), int(rango[0][3]) + 1):
                    l += ['{' + rango[0][0] + str(i) + rango[0][4] + '}']

                l = '( ' + (' ' + rango[0][1] + ' ').join(l) + ' )'
                formula = formula.replace('{' + var_f + '}', l)

            vars_formula = re.findall(r"\{([^\}]*)\}", formula)
            vars_formula = list(dict.fromkeys(vars_formula))

            formula = "{" + var + "} = " + formula

            vars = []
            for var_f in vars_formula:
                if var_f not in evals:
                    vars.append(var_f)

            DB.insert_formula(curso_id, formula)

            return vars
            print("Fórmula agregada exitosamente.")
        except ValueError:
            print("Error en los datos ingresados. Intenta nuevamente.")
            input("\nPresiona Enter para continuar...")


def modificar_formulas(curso_id):
    while True:
        os.system('clear')
        print("\n--- Modificar Fórmulas ---")
        formulas = DB.get_formulas(curso_id)

        evaluaciones = DB.obtener_evaluaciones_curso(curso_id)

        if not evaluaciones:
            print("No hay evaluaciones registradas para este curso.")
            input("\nPresiona Enter para continuar...")
            return

        headers = ["ID", "Evaluación"]
        data = [[eva['id'], eva['nombre']] for eva in evaluaciones]
        max_lens = [5, 20]
        table = Table(headers=headers, data=data, max_lens=max_lens)
        print(table)

        if formulas:
            headers = ["ID", "Fórmula"]
            data = [[formula['id'], formula['formula']] for formula in formulas]
            max_lens = [5, 100]
            table = Table(headers=headers, data=data, max_lens=max_lens)
            print(table)

        opcion = input(
            "\n1. Reescribir formulas\n2. Volver\n\nElige una opción: ")

        evals = [eva['nombre'] for eva in evaluaciones]

        if opcion == "1":
            # Eliminar todas las formulas
            DB.eliminar_formulas(curso_id)

            # Agregar nuevas formulas
            variables = ["NP"]
            while variables:
                os.system('clear')
                print("\n--- Reescribiendo Fórmulas ---")
                formulas = DB.get_formulas(curso_id)

                headers = ["ID", "Evaluación"]
                data = [[eva['id'], eva['nombre']] for eva in evaluaciones]
                max_lens = [5, 20]
                table = Table(headers=headers, data=data, max_lens=max_lens)
                print(table)

                if formulas:
                    headers = ["ID", "Fórmula"]
                    data = [[formula['id'], formula['formula']] for formula in formulas]
                    max_lens = [5, 100]
                    table = Table(headers=headers, data=data, max_lens=max_lens)
                    print(table)

                print(f"Variables: {", ".join(variables)}")

                var = variables.pop(0)
                variables_ = agregar_formula(curso_id, evals, var=var)

                variables += variables_

                # Eliminar duplicados
                variables = list(dict.fromkeys(variables))
        else:
            return


def modificar_restricciones(curso_id):
    while True:
        os.system('clear')
        print("\n--- Modificar Restricciones ---")
        formulas = DB.get_formulas(curso_id)
        evaluaciones = DB.obtener_evaluaciones_curso(curso_id)
        restricciones = DB.get_restricciones(curso_id)

        if not evaluaciones:
            print("No hay evaluaciones registradas para este curso.")
            input("\nPresiona Enter para continuar...")
            return

        if not formulas:
            print("No hay formulas registradas para este curso.")
            input("\nPresiona Enter para continuar...")
            return

        headers = ["ID", "Evaluación"]
        data = [[eva['id'], eva['nombre']] for eva in evaluaciones]
        max_lens = [5, 20]
        table = Table(headers=headers, data=data, max_lens=max_lens)
        print(table)

        headers = ["ID", "Fórmula"]
        data = [[formula['id'], formula['formula']] for formula in formulas]
        max_lens = [5, 100]
        table = Table(headers=headers, data=data, max_lens=max_lens)
        print(table)

        if restricciones:
            headers = ["ID", "Restricción"]
            data = [[restriccion['id'], restriccion['restriccion']] for restriccion in restricciones]
            max_lens = [5, 100]
            table = Table(headers=headers, data=data, max_lens=max_lens)
            print(table)

        opcion = input(
            "\n1. Agregar restricción\n2. Eliminar restricción\n3. Volver\n\nElige una opción: ")

        evals = [eva['nombre'] for eva in evaluaciones]
        variables = [formula['formula'].split(' = ')[0] for formula in formulas]

        if opcion == "1":
            os.system('clear')
            print("\n--- Reescribiendo Restricciones ---")
            restricciones = DB.get_restricciones(curso_id)

            if restricciones:
                headers = ["ID", "Restricción"]
                data = [[restriccion['id'], restriccion['restriccion']] for restriccion in restricciones]
                max_lens = [5, 100]
                table = Table(headers=headers, data=data, max_lens=max_lens)
                print(table)

            print(f"Evaluaciones: {", ".join(evals)}")
            print(f"Variables: {", ".join(variables)}")

            restriccion = input("Ingresa la restricción [h para ayuda]: ")

            if restriccion == "h":
                print(
                    "Formato: {<nombre_variable> o formula arbitraria de evaluaciones} [ > | < | >= | <= | = ] {<valor>}")
                print('''Ejemplo:
{NP} >= 4
{Certamen 1} + {Tarea 1} < 20\n''')
                restriccion = input("Ingresa la restricción: ")

            if not re.match(r".* [><=]{1,2} [0-9]+", restriccion):
                print("Formato incorrecto. Inténtalo de nuevo.")
                input("\nPresiona Enter para continuar...")
                continue

            DB.insert_restriccion(curso_id, restriccion)
            print("Restricción agregada exitosamente.")
        elif opcion == "2":
            if not restricciones:
                print("No hay restricciones registradas para este curso.")
                input("\nPresiona Enter para continuar...")
                return
            try:
                restriccion_id = int(input("\nIngresa el ID de la restricción a eliminar: "))
                DB.eliminar_restriccion(restriccion_id)
                print("Restricción eliminada exitosamente.")
            except ValueError:
                print("ID no válido. Inténtalo de nuevo.")
                input("\nPresiona Enter para continuar...")
        else:
            return

def optimizar_notas(curso_id):
    curso = DB.get_curso(curso_id)
    if not curso:
        print("El curso seleccionado no existe.")
        return

    evaluaciones = DB.get_notas_evaluaciones(curso_id)
    formulas = DB.get_formulas_optimizacion(curso_id)
    restricciones = DB.get_restricciones_optimizacion(curso_id)

    if not evaluaciones:
        print("No hay evaluaciones registradas para este curso.")
        input("\nPresiona Enter para continuar...")
        return

    if not formulas:
        print("No hay formulas registradas para este curso.")
        input("\nPresiona Enter para continuar...")
        return

    if not restricciones:
        restricciones = None


    curso = Curso(formulas, restricciones)

    res = curso.optimize(evals=evaluaciones)
    curso.printData(res['x'][:len(evaluaciones)])

    print("Notas optimizadas exitosamente.")
    input("\nPresiona Enter para continuar...")

def mostrar_detalle_curso(curso_id):
    opcion = None
    while opcion != "4":
        try:
            os.system('clear')
            curso = DB.get_curso(curso_id)  # Devuelve un diccionario con la información del curso
            evaluaciones = DB.obtener_proximas_evaluaciones_curso(curso_id,
                                                                  limite=5)  # Devuelve una lista con las evaluaciones más cercanas

            if not curso:
                print("El curso seleccionado no existe.")
                return

            headers_curso = ["ID", "Nombre", "Semestre", "Créditos", "Nota Actual", "Nota Máxima", "P(Aprobar)", "Objetivo",
                             "P(Objetivo)"]
            data_curso = [[
                curso['id'], curso['nombre'], f"{curso['anio']}-{curso['semestre']}", curso['creditos'],
                curso['nota'], curso['nota_max'], f"{curso['prob_aprobar']:.2f}%",
                curso['nota_objetivo'], f"{curso['prob_objetivo']:.2f}%"
            ]]
            max_lens_curso = [6, 20, 8, 8, 12, 12, 12, 12, 12]

            print(f"\n--- Detalles del Curso: {curso['nombre']} ---")
            table_curso = Table(headers=headers_curso, data=data_curso, max_lens=max_lens_curso)
            print(table_curso)

            print("\n--- Próximas Evaluaciones ---")
            if not evaluaciones:
                print("No hay evaluaciones próximas registradas.")
            else:
                headers = ["Evaluación", "Fecha", "Nota"]
                data = [[eva['nombre'], eva['fecha'], eva['nota']] for eva in evaluaciones]
                max_lens = [20, 10, 10, 10, 15]
                table = Table(headers=headers, data=data, max_lens=max_lens)
                print(table)

            print('''
        1. Modificar evaluaciones
        2. Modificar formulas
        3. Modificar restricciones
        4. Optimizar notas
        ''')
            opcion = input("Elige una opción: ")

            if opcion == "1":
                modificar_evaluaciones(curso_id)
            elif opcion == "2":
                modificar_formulas(curso_id)
            elif opcion == "3":
                modificar_restricciones(curso_id)
            elif opcion == "4":
                optimizar_notas(curso_id)
            else:
                return
        except Exception as e:
            print(e)
            input("\nPresiona Enter para continuar...")


def agregar_curso():
    os.system('clear')
    print("\n--- Agregar Curso ---")
    cfg = config()
    try:
        nombre = input("Nombre del curso: ")
        anio_actual = datetime.date.today().year
        semestre_actual = 1 if datetime.date.today().month <= 6 else 2
        objetivo_actual = cfg.get_nota_objetivo()
        anio = input(f"Año [Por defecto: {anio_actual}]: ") or anio_actual
        semestre = input(f"Semestre (1 o 2) [Por defecto: {semestre_actual}]: ") or semestre_actual
        nota_objetivo = input(f"Nota objetivo [Por defecto: {objetivo_actual}]: ") or objetivo_actual
        creditos = int(input("Créditos: "))

        confirmacion = input(f"\n¿Deseas agregar el curso {nombre} con los siguientes datos?\n"
                             f"Año: {anio}\n"
                             f"Semestre: {semestre}\n"
                             f"Nota Objetivo: {nota_objetivo}\n"
                             f"Créditos: {creditos}\n"
                             "S/N: ")

        if confirmacion.lower() != "s":
            print("Operación cancelada.")
            return

        # Aquí llamarías a la función para insertar el curso en la base de datos
        DB.insert_curso(nombre, int(anio), int(semestre), creditos, nota_objetivo=nota_objetivo)
        print("Curso agregado exitosamente.")
    except ValueError:
        print("Error en los datos ingresados. Intenta nuevamente.")
        input("\nPresiona Enter para continuar...")


def menu_cursos():
    while True:
        os.system('clear')
        cursos = DB.get_cursos(query_type="no_finalizados")
        print("\n--- Menú de Cursos ---")
        if not cursos:
            print("No tienes cursos registrados.")
        else:
            headers = ["ID", "Curso", "Nota Actual", "Probabilidad de Aprobar"]
            data = [[curso['id'], curso['nombre'], curso['nota'], f"{curso['prob_aprobar']:.2f}%"] for curso in cursos]
            max_lens = [5, 20, 15, 25]
            table = Table(headers=headers, data=data, max_lens=max_lens)
            print(table)

        if cursos:
            print("\n1. Seleccionar un curso")
        print("2. Agregar un curso")
        print("3. Eliminar un curso")
        print("4. Volver al menú principal")
        opcion = input("\nElige una opción: ")

        if opcion == "1":
            try:
                curso_id = int(input("\nIngresa el ID del curso: "))
                mostrar_detalle_curso(curso_id)
            except ValueError:
                print("ID no válido. Inténtalo de nuevo.")
                input("\nPresiona Enter para continuar...")
        elif opcion == "2":
            agregar_curso()
        elif opcion == "3":
            print("Función para eliminar un curso (en desarrollo)")
        elif opcion == "4":
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")
            input("\nPresiona Enter para continuar...")


def pantalla_inicial():
    os.system('clear')
    print("=============================")
    print("   Gestor Académico")
    print("=============================")
    mostrar_estado_cursos()
    mostrar_tareas_hoy()
    print("\n1. Menú de Cursos")
    print("2. Ver todas las tareas")
    print("3. Salir")
    opcion = input("\nElige una opción: ")
    return opcion


# Ejemplo de ejecución inicial
if __name__ == "__main__":
    while True:
        opcion = pantalla_inicial()
        if opcion == "1":
            menu_cursos()
        elif opcion == "2":
            print("Función para ver todas las tareas (en desarrollo)")
        elif opcion == "3":
            print("Saliendo del programa.")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")
