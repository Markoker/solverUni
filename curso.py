import time

import sympy
import re
import json
from scipy.optimize import linprog, minimize
from scipy.stats import truncnorm
import numpy as np
from utils import printEquation, printProgressBar, print_bool, printHistogramSuccess
import concurrent.futures
from matplotlib import pyplot as plt


class Curso:
    def __init__(self, formulas, restricciones, forceNonLinear=False):
        self.formulas = formulas
        self.restricciones = restricciones
        self.formula = None
        self.vars = None
        self.symbols = None

        self.format_formulas()
        self.isLinear = self.is_linear()

        if forceNonLinear:
            self.isLinear = False

        self.optimize = self.linearOptimization if self.isLinear else self.nonlinear_optimization

        self.formula_func = sympy.lambdify(self.symbols, self.formula, modules='numpy')
        self.restriccion_funcs = [
            (sympy.lambdify(self.symbols, restriccion[0], modules='numpy'), restriccion[1], restriccion[2])
            for restriccion in self.restricciones
        ]

    def get_vars(self, formula):
        vars = re.findall(r"\{([^\}]*)\}", formula)

        # Remove duplicates from list keeping order
        vars = list(dict.fromkeys(vars))

        return vars

    def is_linear(self):
        # Obtener los términos de la fórmula
        terms = self.formula.as_ordered_terms()

        # Verificar si todos los términos son de primer grado
        for term in terms:
            if any(symbol in term.free_symbols and term.as_coeff_exponent(symbol)[1] != 1 for symbol in self.symbols):
                return False
            if len(term.free_symbols) > 1:
                return False
        return True

    def printData(self, values):
        if len(values) != len(self.vars):
            print("Error en la cantidad de valores")
            return

        sub = {}
        for i in range(len(values)):
            sub[self.symbols[i]] = values[i]
        print("Evaluaciones:")
        for i in range(len(self.vars)):
            print(f"{self.vars[i]}: {values[i]:.2f}")
        print()

        formula_str = str(self.formula)

        for i in range(len(self.vars)):
            evalReplace = "[" + self.vars[i] + "]"

            formula_str = formula_str.replace(f"x{i}", evalReplace)

        print(f"NP = {formula_str} = {self.formula.subs(sub):.2f}\n")

        if self.restricciones is None or len(self.restricciones) == 0:
            return

        print("Restricciones:")
        for restriccion in self.restricciones:
            r = restriccion[0]

            r_str = str(r)

            for i in range(len(self.vars)):
                evalReplace = "[" + self.vars[i] + "]"

                r_str = r_str.replace(f"x{i}", evalReplace)

            if restriccion[2] == 1:
                print(f"{r_str} = {r.subs(sub):.0f} <= {restriccion[1]}")
            elif restriccion[2] == -1:
                print(f"{r_str} = {r.subs(sub):.0f} >= {restriccion[1]}")
            elif restriccion[2] == 0:
                print(f"{r_str} = {r.subs(sub):.0f} = {restriccion[1]}")

    def __str__(self):
        return f"Formulas: {self.formulas}\nRestricciones: {self.restricciones}\nFormula: {self.formula} [{"Lineal" if self.isLinear else "No lineal"}]\nVars: {self.vars}\nSymbols: {self.symbols}"

    def format_formulas(self):
        formulas_dict = {}
        formula_main = None

        for f in self.formulas:
            f = f.split("=")
            f[0] = f[0].strip().replace("{", "").replace("}", "")
            f[1] = f[1].strip()
            if f[0] == "NP":
                formula_main = f[1]
            else:
                formulas_dict[f[0]] = f[1]

        vars = self.get_vars(formula_main)

        for variable in vars:
            if variable not in formulas_dict:
                continue

            formula_main = formula_main.replace(f"{{{variable}}}", f"({formulas_dict[variable]})")

        self.vars = self.get_vars(formula_main)
        str_sym = f"x:{len(self.vars)}"
        self.symbols = list(sympy.symbols(str_sym))

        for i, var in enumerate(self.vars):
            formula_main = formula_main.replace('{' + var + '}', f"x{i}")

        self.formula = sympy.sympify(formula_main)

        if self.restricciones is None:
            return

        r = []

        for restriccion in self.restricciones:
            vars_r = self.get_vars(restriccion)

            for variable in vars_r:
                if variable not in formulas_dict:
                    continue

                restriccion = restriccion.replace(f"{{{variable}}}", f"({formulas_dict[variable]})")

            for i, var in enumerate(self.vars):
                restriccion = restriccion.replace('{' + var + '}', f"x{i}")

            ineq = ""

            if "<=" in restriccion:
                ineq = 1
                restriccion = restriccion.split("<=")
            elif ">=" in restriccion:
                ineq = -1
                restriccion = restriccion.split(">=")
            elif "=" in restriccion:
                ineq = 0
                restriccion = restriccion.split("=")
            elif "<" in restriccion:
                ineq = 1
                restriccion = restriccion.split("<")
            elif ">" in restriccion:
                ineq = -1
                restriccion = restriccion.split(">")
            else:
                print("Error en la restricción")
                return

            restriccion = [sympy.sympify(restriccion[0]), sympy.sympify(restriccion[1]), ineq]

            r.append(restriccion)

        self.restricciones = r

    def calcular_nota(self, evals, presupuesto):
        values = {}

        for i, variable in enumerate(self.vars):
            if variable in evals:
                values[self.symbols[i]] = evals[variable]
            else:
                values[self.symbols[i]] = presupuesto

        print(values)

        return self.formula.subs(values)

    def nonlinear_optimization(self, evals=None, objetivo=55, mode="mismoPeso"):
        if self.isLinear:
            return

        l = len(self.symbols)

        f_restricciones = []

        terms = self.formula.as_ordered_terms()

        # Funcion objetivo que minimiza la distancia de las notas entre si
        if mode == "mismaNota":
            def objective(x):
                s = 0
                for i in range(l):
                    if self.vars[i] in evals:
                        continue
                    for j in range(i + 1, l):
                        if self.vars[j] in evals:
                            continue
                        s += (x[i] - x[j]) ** 2
                X = np.array(x)
                return np.sqrt(np.sum(X * X)) + np.var(X)
        else:
            def objective(x):
                vals = {}

                for i in range(l):
                    vals[self.symbols[i]] = x[i]

                X = []
                grad = []

                for i in range(l):
                    if self.vars[i] in evals:
                        continue

                    # Evaluar gradiente y manejar valores indefinidos
                    grad_i = sympy.diff(self.formula, self.symbols[i]).subs(vals)
                    try:
                        grad_i = float(grad_i)  # Convertir a valor numérico
                        if np.isnan(grad_i):
                            grad_i = 1e6  # Sustituir NaN por 0
                    except (TypeError, ValueError):
                        grad_i = 1e6  # Sustituir valores no evaluables por 0

                    grad.append(grad_i)
                    X.append(x[i])

                grad = np.array(grad, dtype=np.float64)  # Asegurar tipo flotante
                X = np.array(X, dtype=np.float64)
                w_grad = grad * X

                # Gestionar valores NaN
                grad = np.nan_to_num(grad, nan=1e6)
                w_grad = np.nan_to_num(w_grad, nan=1e6)
                X = np.nan_to_num(X, nan=1e6)

                # Calcular la función objetivo
                ans = (np.sum(
                    np.array(
                        [(w_grad[i] - w_grad[j]) ** 2
                         for i in range(len(X) - 1)
                         for j in range(i + 1, len(X))]))
                       + np.sum(X))
                return ans

        # Restriccion objetivo, que la nota sea igual a la deseada
        def obj_constraint(x):
            values = {}
            for i, symbol in enumerate(self.symbols):
                values[symbol] = x[i]

            ans = self.formula.subs(values) - objetivo
            return ans

        f_restricciones.append({'type': 'ineq', 'fun': obj_constraint})

        # Restricciones del curso
        if self.restricciones is None:
            self.restricciones = []

        for restriccion in self.restricciones:
            def f(x, restriccion=restriccion):
                values = {}
                for i, symbol in enumerate(self.symbols):
                    values[symbol] = x[i]

                ans = restriccion[0].subs(values) - restriccion[1]

                if restriccion[2] != 0:
                    return ans * -restriccion[2]

                return ans

            if restriccion[2] != 0:
                f_restricciones.append({'type': 'ineq', 'fun': f})
            else:
                f_restricciones.append({'type': 'eq', 'fun': f})

        # Bounds de las Notas
        bounds = [(0, 100) for _ in range(l)]

        # Restricciones de las notas que ya se conocen
        for i in range(l):
            if self.vars[i] in evals:
                def eq_constraint(x, index=i):
                    return x[index] - evals[self.vars[index]]

                f_restricciones.append({'type': 'eq', 'fun': eq_constraint})

        x0 = [100 for _ in range(l)]

        # Replace actual values in x0
        for i, variable in enumerate(self.vars):
            if variable in evals:
                x0[i] = evals[variable]

        return minimize(objective, x0, constraints=f_restricciones, bounds=bounds)

    def linearOptimization(self, evals, objetivo=55, mode="mismoPeso"):
        if not self.isLinear:
            return

        values = {}

        for i, variable in enumerate(self.vars):
            if evals[variable]['nota'] is None:
                continue
            values[self.symbols[i]] = evals[variable]['nota']

        f_opt = self.formula.subs(values)

        terms = f_opt.as_ordered_terms()

        c = [0 for _ in range(len(self.symbols))]

        r = [0 for _ in range(len(self.symbols))]

        # Nota objetivo
        for term in terms:
            if len(term.free_symbols) < 1:
                objetivo -= term
                continue

            sym = list(term.free_symbols)[0]

            if sym in self.symbols:
                index = self.symbols.index(sym)
                r[index] = term.as_coefficients_dict()[sym]
                # c[index] = term.as_coefficients_dict()[sym]

        A_ub = []
        b_ub = []
        A_eq = []
        b_eq = []

        A_eq.append(r)
        b_eq.append(objetivo)

        # Notas que ya se conocen
        for i in range(len(self.vars)):
            if evals[self.vars[i]]['nota'] is None:
                continue

            row = [0 for _ in range(len(self.symbols))]
            row[i] = 1
            A_eq.append(row)
            b_eq.append(evals[self.vars[i]]['nota'])

        # Restricciones del curso
        if self.restricciones is None:
            self.restricciones = []


        for restriccion in self.restricciones:
            row = [0 for _ in range(len(self.symbols))]
            terms_r = restriccion[0].as_ordered_terms()

            for term in terms_r:
                if len(term.free_symbols) < 1:
                    restriccion[1] -= term
                    continue

                sym = list(term.free_symbols)[0]

                if sym in self.symbols:
                    index = self.symbols.index(sym)
                    row[index] = term.as_coefficients_dict()[sym] * restriccion[2]

            A_ub.append(row)
            b_ub.append(restriccion[1] * restriccion[2])

        # Restricciones de balance
        count = len(self.vars) + 1
        for i in range(len(self.symbols)):
            if evals[self.vars[i]]['nota'] is None:
                continue

            for j in range(i + 1, len(self.symbols)):
                if evals[self.vars[j]]['nota'] is None:
                    continue

                row = [0 for _ in range(count)]

                sym_i = self.symbols[i]
                sym_j = self.symbols[j]

                ti, tj = 0, 0

                # Get coefficient of each term 
                for term in terms:
                    if sym_i in term.free_symbols:
                        ti = term.as_coefficients_dict()[sym_i]
                    if sym_j in term.free_symbols:
                        tj = term.as_coefficients_dict()[sym_j]

                if mode == "mismoPeso":
                    row[i] = ti
                    row[j] = -tj
                elif mode == "mismaNota":
                    row[i] = 1
                    row[j] = -1
                else:
                    row[i] = 1
                    row[j] = -1

                row[-1] = -1

                for rowA in A_eq:
                    rowA.append(0)

                for rowA in A_ub:
                    rowA.append(0)

                A_ub.append(row)
                b_ub.append(0)

                alter_row = row.copy()
                alter_row[i] *= -1
                alter_row[j] *= -1
                alter_row[-1] = -1

                A_ub.append(alter_row)
                b_ub.append(0)

                c.append(1)
                count += 1

        bounds = [(evals[k]['min'], evals[k]['max']) for k in evals]

        res = linprog(c, A_ub, b_ub, A_eq, b_eq, bounds=bounds, method='highs', options={"disp": False})

        return res

    def success(self, symbol_values, value):
        args = [symbol_values[symbol] for symbol in self.symbols]

        NP = self.formula_func(*args)

        if NP < value:
            return False, 

        for func, lim, tipo in self.restriccion_funcs:
            result = func(*args)
            if tipo == 1 and result > lim:
                return False, NP
            if tipo == -1 and result < lim:
                return False, NP
            if tipo == 0 and result != lim:
                return False, NP

        return True, NP

    def success_vectorized(self, symbol_values_list, value):
        # Convierte symbol_values_list a un arreglo de numpy para las variables simbólicas
        args_matrix = np.array([[values[symbol] for symbol in self.symbols] for values in symbol_values_list])

        # Evalúa la fórmula principal en vector
        formula_results = self.formula_func(*args_matrix.T)
        valid_formula = formula_results >= value

        # Evalúa restricciones
        valid_restrictions = np.ones(len(symbol_values_list), dtype=bool)
        for func, lim, tipo in self.restriccion_funcs:
            results = func(*args_matrix.T)
            if tipo == 1:
                valid_restrictions &= results <= lim
            elif tipo == -1:
                valid_restrictions &= results >= lim
            elif tipo == 0:
                valid_restrictions &= results == lim

        return valid_formula & valid_restrictions, formula_results

    def successProbability(self, evals, value, distribution, n=10000):
        # Preprocesa las variables conocidas
        symbol_values = {self.symbols[i]: evals[variable] for i, variable in enumerate(self.vars) if variable in evals}
        no_evaluadas = [self.symbols[i] for i, variable in enumerate(self.vars) if variable not in evals]

        # Si no hay variables por evaluar, calcula directamente
        if len(no_evaluadas) == 0:
            return self.success(symbol_values, value)

        # Genera muestras para las variables no evaluadas
        samples = {symbol: np.array([distribution() for _ in range(n)]) for symbol in no_evaluadas}

        # Construye un arreglo de entradas para todas las simulaciones
        symbol_values_list = []
        for i in range(n):
            sample = symbol_values.copy()
            for symbol in no_evaluadas:
                sample[symbol] = samples[symbol][i]
            symbol_values_list.append(sample)

        return self.success_vectorized(symbol_values_list, value)
