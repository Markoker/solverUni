import sqlite3

class BBDD:
    def __init__(self):
        self.conexion = sqlite3.connect("bbdd.db")
        self.cursor = self.conexion.cursor()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS asignaturas(
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                nombre TEXT UNIQUE NOT NULL,
                                aprobar REAL,                -- Probabilidad de aprobar
                                nota_70 REAL,                -- Probabilidad de obtener una nota mayor o igual a 70
                                media_notas REAL,            -- Media general de notas de la asignatura
                                desviacion_notas REAL,       -- Desviación estándar de notas
                                nota_minima REAL,            -- Nota mínima obtenible
                                nota_maxima REAL             -- Nota máxima obtenible
                            );''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS evaluaciones(
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                asignatura_id INTEGER NOT NULL,
                                nombre TEXT NOT NULL,           -- Nombre de la evaluación (por ejemplo: 'Certamen 1', 'Tarea 1')
                                fecha DATE,            -- Fecha de la evaluación
                                valor REAL,                     -- Valor de la evaluación (puede ser NULL hasta que se califique)
                                FOREIGN KEY (asignatura_id) REFERENCES asignaturas(id) ON DELETE CASCADE
                            );''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS formulas (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                asignatura_id INTEGER NOT NULL,          
                                expresion TEXT NOT NULL,        -- Expresión de la fórmula
                                FOREIGN KEY (asignatura_id) REFERENCES asignaturas(id) ON DELETE CASCADE
                            );''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS restricciones (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                                asignatura_id INTEGER NOT NULL,
                                expresion TEXT NOT NULL,        -- Expresión de la restricción
                                FOREIGN KEY (asignatura_id) REFERENCES asignaturas(id) ON DELETE CASCADE
                            );''')
        self.conexion.commit()

    def __del__(self):
        self.conexion.close()

#region GETTERS
    def get_asignaturas(self):
        '''
        Retorna todas las asignaturas de la base de datos
        '''
        self.cursor.execute("SELECT * FROM asignaturas")
        return self.cursor.fetchall()

    def get_asignaturas_actuales(self):
        '''
        Retorna todas las asignaturas que tienen alguna evaluación sin nota asignada
        '''
        self.cursor.execute("SELECT DISTINCT asignaturas.* FROM asignaturas JOIN evaluaciones ON asignaturas.id = evaluaciones.asignatura_id WHERE evaluaciones.valor IS NULL")
        return self.cursor.fetchall()

    def get_asignaturas_pasadas(self):
        '''
        Retorna todas las asignaturas que no tienen ninguna evaluación sin nota asignada
        '''
        self.cursor.execute("SELECT a.* FROM asignaturas a WHERE NOT EXISTS (SELECT * FROM evaluaciones e WHERE a.id = e.asignatura_id AND e.valor IS NULL)")
        return self.cursor.fetchall()

    def get_asignatura(self, id):
        '''
        Retorna la asignatura con el id especificado
        @param id: id de la asignatura
        '''
        self.cursor.execute("SELECT * FROM asignaturas WHERE id = ?", (id,))
        return self.cursor.fetchone()

    def get_proximas_evaluaciones(self):
        '''
        Retorna las próximas evaluaciones a realizar ordenadas por fecha
        '''
        self.cursor.execute("SELECT * FROM evaluaciones WHERE fecha >= date('now') ORDER BY fecha")
        return self.cursor.fetchall()

    def get_evaluaciones(self, asignatura_id):
        '''
        Retorna todas las evaluaciones de la asignatura especificada
        @param asignatura_id: id de la asignatura
        '''
        self.cursor.execute("SELECT * FROM evaluaciones WHERE asignatura_id = ?", (asignatura_id,))
        return self.cursor.fetchall()

    def get_notas_evaluaciones(self):
        '''
        Retorna todas las evaluaciones que tienen nota asignada
        '''
        self.cursor.execute("SELECT valor FROM evaluaciones WHERE valor IS NOT NULL")
        return self.cursor.fetchall()

    def get_evaluacion(self, id):
        '''
        Retorna la evaluación con el id especificado
        @param id: id de la evaluación
        '''
        self.cursor.execute("SELECT * FROM evaluaciones WHERE id = ?", (id,))
        return self.cursor.fetchone()

    def get_evaluacion_nombre(self, asignatura_id, nombre):
        '''
        Retorna la evaluación con el nombre especificado
        @param asignatura_id: id de la asignatura
        @param nombre: nombre de la evaluación
        '''
        self.cursor.execute("SELECT * FROM evaluaciones WHERE asignatura_id = ? AND nombre = ?", (asignatura_id, nombre))
        return self.cursor.fetchone()

    def get_formulas(self, asignatura_id):
        '''
        Retorna todas las fórmulas de la asignatura especificada (Solo retorna la columna 'expresion')
        @param asignatura_id: id de la asignatura
        '''
        self.cursor.execute("SELECT expresion FROM formulas WHERE asignatura_id = ?", (asignatura_id,))
        return self.cursor.fetchall()

    def get_all_formulas(self, asignatura_id):
        '''
        Retorna todas las fórmulas de la asignatura especificada
        @param asignatura_id: id de la asignatura
        '''
        self.cursor.execute("SELECT * FROM formulas WHERE asignatura_id = ?", (asignatura_id,))
        return self.cursor.fetchall()

    def get_restricciones(self, asignatura_id):
        '''
        Retorna todas las restricciones de la asignatura especificada
        @param asignatura_id: id de la asignatura
        '''
        self.cursor.execute("SELECT expresion FROM restricciones WHERE asignatura_id = ?", (asignatura_id,))
        return self.cursor.fetchall()

    def get_all_restricciones(self, asignatura_id):
        '''
        Retorna todas las restricciones de la asignatura especificada
        @param asignatura_id: id de la asignatura
        '''
        self.cursor.execute("SELECT * FROM restricciones WHERE asignatura_id = ?", (asignatura_id,))
        return self.cursor.fetchall()

    def get_evaluaciones_rango_nota(self, asignatura_id, nota_minima=0, nota_maxima=100):
        '''
        Retorna todas las evaluaciones de la asignatura especificada que tienen nota asignada entre nota_minima y nota_maxima
        @param asignatura_id: id de la asignatura
        '''
        self.cursor.execute("SELECT * FROM evaluaciones WHERE asignatura_id = ? AND valor IS NOT NULL AND valor >= ? AND valor <= ?", (asignatura_id, nota_minima, nota_maxima))
        return self.cursor.fetchall()

    def get_evaluaciones_sin_nota(self, asignatura_id):
        '''
        Retorna todas las evaluaciones de la asignatura especificada que no tienen nota asignada
        @param asignatura_id: id de la asignatura
        '''
        self.cursor.execute("SELECT * FROM evaluaciones WHERE asignatura_id = ? AND valor IS NULL", (asignatura_id,))
        return self.cursor.fetchall()
#endregion
            
#region CREATE
    def create_asignatura(self, nombre):
        '''
        Crea una nueva asignatura con el nombre especificado
        @param nombre: nombre de la asignatura
        '''
        self.cursor.execute("INSERT INTO asignaturas (nombre) VALUES (?)", (nombre,))
        self.conexion.commit()
        return self.cursor.lastrowid

    def create_evaluacion(self, asignatura_id, nombre, fecha=None, valor=None):
        '''
        Crea una nueva evaluación para la asignatura especificada
        @param asignatura_id: id de la asignatura 
        @param nombre: nombre de la evaluación
        @param fecha: fecha de la evaluación 
        @param valor: valor de la evaluación (puede ser None hasta que se califique)
        '''

        self.cursor.execute("INSERT INTO evaluaciones (asignatura_id, nombre, fecha, valor) VALUES (?, ?, ?, ?)", (asignatura_id, nombre, fecha, valor))
        self.conexion.commit()
        return self.cursor.lastrowid

    def create_formula(self, asignatura_id, expresion):
        '''
        Crea una nueva fórmula para la asignatura especificada
        @param asignatura_id: id de la asignatura 
        @param expresion: expresión de la fórmula
        '''
        self.cursor.execute("INSERT INTO formulas (asignatura_id, expresion) VALUES (?, ?)", (asignatura_id, expresion))
        self.conexion.commit()
        return self.cursor.lastrowid

    def create_restriccion(self, asignatura_id, expresion):
        '''
        Crea una nueva restricción para la asignatura especificada
        @param asignatura_id: id de la asignatura 
        @param expresion: expresión de la restricción
        '''
        self.cursor.execute("INSERT INTO restricciones (asignatura_id, expresion) VALUES (?, ?)", (asignatura_id, expresion))
        self.conexion.commit()
        return self.cursor.lastrowid
#endregion

#region UPDATE
    def update_data_asignatura(self, id, aprobar, nota_70, media_notas, desviacion_notas, nota_minima, nota_maxima):
        '''
        Actualiza los datos de la asignatura especificada
        @param id: id de la asignatura
        @param aprobar: probabilidad de aprobar
        @param nota_70: probabilidad de obtener una nota mayor o igual a 70
        @param media_notas: media general de notas de la asignatura
        @param desviacion_notas: desviación estándar de notas
        @param nota_minima: nota mínima obtenible
        @param nota_maxima: nota máxima obtenible
        '''
        self.cursor.execute("UPDATE asignaturas SET aprobar = ?, nota_70 = ?, media_notas = ?, desviacion_notas = ?, nota_minima = ?, nota_maxima = ? WHERE id = ?", (aprobar, nota_70, media_notas, desviacion_notas, nota_minima, nota_maxima, id))
        self.conexion.commit()  
        return self.cursor.lastrowid

    def update_fecha_evaluacion(self, id, fecha):
        '''
        Actualiza la fecha de la evaluación especificada
        @param id: id de la evaluación
        @param fecha: fecha de la evaluación
        '''
        self.cursor.execute("UPDATE evaluaciones SET fecha = ? WHERE id = ?", (fecha, id))
        self.conexion.commit()
        return self.cursor.lastrowid

    def update_valor_evaluacion(self, id, valor):
        '''
        Actualiza el valor de la evaluación especificada
        @param id: id de la evaluación
        @param valor: valor de la evaluación
        '''
        self.cursor.execute("UPDATE evaluaciones SET valor = ? WHERE id = ?", (valor, id))
        self.conexion.commit()
        return self.cursor.lastrowid

    def update_expresion_formula(self, id, expresion):
        '''
        Actualiza la expresión de la fórmula especificada
        @param id: id de la fórmula
        @param expresion: expresión de la fórmula
        '''
        self.cursor.execute("UPDATE formulas SET expresion = ? WHERE id = ?", (expresion, id))
        self.conexion.commit()
        return self.cursor.lastrowid

    def update_expresion_restriccion(self, id, expresion):
        '''
        Actualiza la expresión de la restricción especificada
        @param id: id de la restricción
        @param expresion: expresión de la restricción
        '''
        self.cursor.execute("UPDATE restricciones SET expresion = ? WHERE id = ?", (expresion, id))
        self.conexion.commit()
        return self.cursor.lastrowid

#endregion

#region DELETE
    def delete_asignatura(self, id):
        '''
        Elimina la asignatura especificada
        @param id: id de la asignatura
        '''
        self.cursor.execute("DELETE FROM asignaturas WHERE id = ?", (id,))
        self.conexion.commit()
    
    def delete_evaluacion(self, id):
        '''
        Elimina la evaluación especificada
        @param id: id de la evaluación
        '''
        self.cursor.execute("DELETE FROM evaluaciones WHERE id = ?", (id,))
        self.conexion.commit()

    def delete_formulas(self, asignatura_id):
        '''
        Elimina todas las fórmulas de la asignatura especificada
        @param asignatura_id: id de la asignatura
        '''
        self.cursor.execute("DELETE FROM formulas WHERE asignatura_id = ?", (asignatura_id,))
        self.conexion.commit()

    def delete_formula(self, id):
        '''
        Elimina la fórmula especificada
        @param id: id de la fórmula
        '''
        self.cursor.execute("DELETE FROM formulas WHERE id = ?", (id,))
        self.conexion.commit()

    def delete_restricciones(self, asignatura_id):
        '''
        Elimina todas las restricciones de la asignatura especificada
        @param asignatura_id: id de la asignatura
        '''
        self.cursor.execute("DELETE FROM restricciones WHERE asignatura_id = ?", (asignatura_id,))
        self.conexion.commit()

    def delete_restriccion(self, id):
        '''
        Elimina la restricción especificada
        @param id: id de la restricción
        '''
        self.cursor.execute("DELETE FROM restricciones WHERE id = ?", (id,))
        self.conexion.commit()

#endregion
