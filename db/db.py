from config import config
import sqlite3 as sql 
from random import randint, random
import datetime

class db:
    def __init__(self):
        self.conn = sql.connect('db/db.sqlite3')
        self.cursor = self.conn.cursor()

        self.init_db()

    def get_conn(self):
        return self.conn 

    def __del__(self):
        self.conn.close()

    def init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS curso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,            
                anio INTEGER NOT NULL,
                semestre INTEGER NOT NULL,
                creditos INTEGER NOT NULL,
                nota REAL NOT NULL,
                nota_max REAL NOT NULL,
                prob_aprobar REAL NOT NULL,
                prob_objetivo REAL NOT NULL,
        nota_objetivo REAL NOT NULL,
                finalizado BOOLEAN NOT NULL DEFAULT FALSE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS formula (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER NOT NULL,
                formula TEXT NOT NULL,
                FOREIGN KEY (curso_id) REFERENCES curso(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS restriccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER NOT NULL,
                restriccion TEXT NOT NULL,
                FOREIGN KEY (curso_id) REFERENCES curso(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                fecha DATE,
                nota REAL,
                min REAL NOT NULL,
                max REAL NOT NULL,
                FOREIGN KEY (curso_id) REFERENCES curso(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS to_do (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER,
                nombre TEXT NOT NULL,
                dias TEXT NOT NULL DEFAULT '[0, 0, 0, 0, 0, 0, 0]',
                activa BOOLEAN NOT NULL DEFAULT TRUE,
                                
                FOREIGN KEY (curso_id) REFERENCES curso(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tarea (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                to_do_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                fecha DATE NOT NULL,
                completada BOOLEAN NOT NULL DEFAULT FALSE,
                FOREIGN KEY (to_do_id) REFERENCES to_do(id)
            )
        ''')

        self.conn.commit()

    # GET
    def get_cursos(self, query_type="all"):
        cfg = config()

        if query_type == "all":
            self.cursor.execute('''
                SELECT * FROM curso
            ''')
        elif query_type == "finalizados":
            self.cursor.execute('''
                SELECT * FROM curso WHERE finalizado = 1
            ''')
        elif query_type == "no_finalizados":
            self.cursor.execute('''
                SELECT * FROM curso WHERE finalizado = 0
            ''')
        elif query_type == "aprobados":
            self.cursor.execute('''
                SELECT * FROM curso WHERE nota >= ? AND finalizado = 1
            ''', (cfg.get_nota_aprobar(),))
        elif query_type == "no_aprobados":
            self.cursor.execute('''
                SELECT * FROM curso WHERE nota < ? AND finalizado = 1
            ''', (cfg.get_nota_aprobar(),))
        elif query_type == "objetivo":
            self.cursor.execute('''
                SELECT * FROM curso WHERE nota >= nota_objetivo AND finalizado = 1 
            ''')
        elif query_type == "no_objetivo":
            self.cursor.execute('''
                SELECT * FROM curso WHERE nota < nota_objetivo AND finalizado = 1
            ''')
        else:
            print('''Query invalido. Las opciones son:''')
            print('''- all: Todos los cursos''')
            print('''- finalizados: Cursos finalizados''')
            print('''- no_finalizados: Cursos no finalizados''')
            print('''- aprobados: Cursos aprobados''')
            print('''- no_aprobados: Cursos no aprobados''')
            print('''- objetivo: Cursos en los que se alcanzo el objetivo''') 
            print('''- no_objetivo: Cursos en los que no se alcanzo el objetivo''')
            return None
        cursos = self.cursor.fetchall()

        rows = [
            {
                'id': curso[0],
                'nombre': curso[1],
                'anio': curso[2],
                'semestre': curso[3],
                'creditos': curso[4],
                'nota': curso[5],
                'nota_max': curso[6],
                'prob_aprobar': curso[7],
                'prob_objetivo': curso[8],
                'nota_objetivo': curso[9],
                'finalizado': curso[10]
            } for curso in cursos
        ]
        return rows

    def get_curso(self, id):
        self.cursor.execute('''
            SELECT * FROM curso WHERE id = ?
        ''', (id,))
        curso = self.cursor.fetchone()
        return {
            'id': curso[0],
            'nombre': curso[1],
            'anio': curso[2],
            'semestre': curso[3],
            'creditos': curso[4],
            'nota': curso[5],
            'nota_max': curso[6],
            'prob_aprobar': curso[7],
            'prob_objetivo': curso[8],
            'nota_objetivo': curso[9],
            'finalizado': curso[10]
        }

    def obtener_tareas_hoy(self):
        self.cursor.execute('''
            SELECT t.id, t.nombre, c.nombre, t.completada 
            FROM tarea t
            JOIN to_do td ON t.to_do_id = td.id
            JOIN curso c ON td.curso_id = c.id
            WHERE t.fecha = ?
        ''', (datetime.date.today(),))
        tareas = self.cursor.fetchall()

        return [
            {
                'id': tarea[0],
                'nombre': tarea[1],
                'curso': tarea[2],
                'completada': tarea[3]
            } for tarea in tareas
        ]

    def obtener_proximas_evaluaciones_curso(self, curso_id, limite=5):
        self.cursor.execute('''
            SELECT * FROM evaluacion WHERE curso_id = ? AND (fecha >= ? OR fecha IS NULL)
        ''', (curso_id, datetime.date.today()))

        evaluaciones = self.cursor.fetchall()[:limite]

        return [
            {
                'id': eva[0],
                'nombre': eva[2],
                'nota': eva[4],
                'min': eva[5],
                'max': eva[6],
                'fecha': eva[3]
            } for eva in evaluaciones
        ]

    def obtener_evaluaciones_curso(self, curso_id):
        self.cursor.execute('''
            SELECT * FROM evaluacion WHERE curso_id = ?
        ''', (curso_id,))
        evaluaciones = self.cursor.fetchall()

        return [
            {
                'id': eva[0],
                'nombre': eva[2],
                'nota': eva[4],
                'min': eva[5],
                'max': eva[6],
                'fecha': eva[3]
            } for eva in evaluaciones
        ]

    def get_formulas(self, curso_id):
        self.cursor.execute('''
            SELECT id, formula FROM formula WHERE curso_id = ?
        ''', (curso_id,))
        formulas = self.cursor.fetchall()

        return [{
            'id': formula[0],
            'formula': formula[1]
        }
        for formula in formulas]

    def get_restricciones(self, curso_id):
        self.cursor.execute('''
            SELECT id, restriccion FROM restriccion WHERE curso_id = ?
        ''', (curso_id,))
        restricciones = self.cursor.fetchall()

        return [{
            'id': restriccion[0],
            'restriccion': restriccion[1]
        }
        for restriccion in restricciones]

    def get_formulas_optimizacion(self, curso_id):
        self.cursor.execute('''
            SELECT formula FROM formula WHERE curso_id = ?
        ''', (curso_id,))
        formulas = self.cursor.fetchall()

        return [formula[0] for formula in formulas]

    def get_restricciones_optimizacion(self, curso_id):
        self.cursor.execute('''
            SELECT restriccion FROM restriccion WHERE curso_id = ?
        ''', (curso_id,))
        restricciones = self.cursor.fetchall()

        return [restriccion[0] for restriccion in restricciones]

    def get_notas_evaluaciones(self, curso_id):
        self.cursor.execute('''
            SELECT nombre, nota, min, max FROM evaluacion WHERE curso_id = ?
        ''', (curso_id,))

        evaluaciones = self.cursor.fetchall()

        return {
            eva[0]: {'nota': eva[1], 'min': eva[2], 'max': eva[3]} for eva in evaluaciones
        }

    # INSERT
    def insert_curso(self, nombre, anio, semestre, creditos, nota=0, nota_max=100, prob_aprobar=0, prob_objetivo=0, nota_objetivo=None, finalizado=0):
        cfg = config()

        if nota_objetivo is None:
            nota_objetivo = cfg.get_nota_objetivo()

        self.cursor.execute('''
            INSERT INTO curso (nombre, anio, semestre, creditos, nota, nota_max, prob_aprobar, prob_objetivo, nota_objetivo, finalizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nombre, anio, semestre, creditos, nota, nota_max, prob_aprobar, prob_objetivo, nota_objetivo, finalizado))

        self.conn.commit()

    def insert_evaluacion(self, curso_id, nombre, min, max, fecha):
        self.cursor.execute('''
            INSERT INTO evaluacion (curso_id, nombre, min, max, fecha)
            VALUES (?, ?, ?, ?, ?)
        ''', (curso_id, nombre, min, max, fecha))

        self.conn.commit()

    def insert_formula(self, curso_id, formula):
        self.cursor.execute('''
            INSERT INTO formula (curso_id, formula)
            VALUES (?, ?)
        ''', (curso_id, formula))

        self.conn.commit()

    def insert_restriccion(self, curso_id, restriccion):
        self.cursor.execute('''
            INSERT INTO restriccion (curso_id, restriccion)
            VALUES (?, ?)
        ''', (curso_id, restriccion))

        self.conn.commit()

    # UPDATE
    def modificar_nota_evaluacion(self, id, nota):
        self.cursor.execute('''
            UPDATE evaluacion SET nota = ? WHERE id = ?
        ''', (nota, id))

        self.conn.commit()

    def modificar_fecha_evaluacion(self, id, fecha):
        self.cursor.execute('''
            UPDATE evaluacion SET fecha = ? WHERE id = ?
        ''', (fecha, id))

        self.conn.commit()

    def modificar_formula(self, id, formula):
        self.cursor.execute('''
            UPDATE formula SET formula = ? WHERE id = ?
        ''', (formula, id))

        self.conn.commit()

    # DELETE
    def eliminar_formulas(self, curso_id):
        self.cursor.execute('''
            DELETE FROM formula WHERE curso_id = ?
        ''', (curso_id,))

        self.conn.commit()

    def eliminar_evaluacion(self, id):
        self.cursor.execute('''
            DELETE FROM evaluacion WHERE id = ?
        ''', (id,))

        self.conn.commit()

    def eliminar_restricciones(self, curso_id):
        self.cursor.execute('''
            DELETE FROM restriccion WHERE curso_id = ?
        ''', (curso_id,))

        self.conn.commit()

    def eliminar_restriccion(self, id):
        self.cursor.execute('''
            DELETE FROM restriccion WHERE id = ?
        ''', (id,))

        self.conn.commit()