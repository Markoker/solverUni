import re
import math as m

class Table:
    def __init__(self, headers, data, max_lens=None):
        self.headers = headers
        self.data = data
        if max_lens is not None:
            self.max_len = max_lens
        else:
            self.max_len = [len(str(h)) for h in headers]

        self.UL = "┌" 
        self.UR = "┐"
        self.DL = "└"
        self.DR = "┘"
        self.H = "─"
        self.V = "│"
        self.C = "┼"
        self.L = "├"
        self.R = "┤"
        self.U = "┬"
        self.D = "┴"

        
        for i, column in enumerate(headers):
            pattern = re.compile(r"\033\[38;5;\d+m(.*)\033\[0m") 
            if pattern.match(str(column)):
                l = len(pattern.match(str(column)).group(1))
            else:
                l = len(str(column))
            if l > self.max_len[i]:
                if pattern.match(str(column)):
                    # Reemplazar unicamente el texto, no los colores
                    self.headers[i] = pattern.match(str(column)).group(1)[:self.max_len[i] - 3] + "..."
                else:
                    self.headers[i] = column[:self.max_len[i] - 3] + "..."
            elif l < self.max_len[i]:
                self.headers[i] = " " * m.ceil((self.max_len[i] - l) / 2) + str(column) + " " * m.floor((self.max_len[i] - l) / 2)



        for i in range(len(data)):
            for j in range(len(data[i])):
                # Center data[i][j] in the cell
                pattern = re.compile(r"\033\[38;5;\d+m(.*)\033\[0m")
                if pattern.match(str(data[i][j])):
                    l = len(pattern.match(str(data[i][j])).group(1))
                else:
                    l = len(str(data[i][j]))

                if l > self.max_len[j]:
                    if pattern.match(str(data[i][j])):
                        # Reemplazar unicamente el texto, no los colores
                        self.data[i][j] = pattern.match(str(data[i][j])).group(1)[:self.max_len[j] - 3] + "..."
                    else:
                        self.data[i][j] = data[i][j][:self.max_len[j] - 3] + "..."
                elif l < self.max_len[j]:
                    self.data[i][j] = " " * m.ceil((self.max_len[j] - l) / 2) + str(data[i][j]) + " " * m.floor((self.max_len[j] - l) / 2)
        
    def __str__(self):
        table = ""
        table += self.UL
        for i, header in enumerate(self.headers):
            table += self.H * (self.max_len[i] + 2)
            if i < len(self.headers) - 1:
                table += self.U
        table += self.UR + "\n"
        for i, header in enumerate(self.headers):
            table += self.V + f" {header} "
        table += self.V + "\n"
        table += self.L
        
        for i, header in enumerate(self.headers):
            table += self.H * (self.max_len[i] + 2)
            if i < len(self.headers) - 1:
                table += self.C 
        table += self.R + "\n" 

        for j, row in enumerate(self.data):
            for i, cell in enumerate(row):
                table += self.V + f" {cell} "
            table += self.V + "\n"
            if j == len(self.data) - 1:
                break
            table += self.L
            for i, cell in enumerate(row):
                table += self.H * (self.max_len[i] + 2)
                if i < len(row) - 1:
                    table += self.C
            table += self.R + "\n"

        table += self.DL 
        for i, header in enumerate(self.headers):
            table += self.H * (self.max_len[i] + 2)
            if i < len(self.headers) - 1:
                table += self.D 
        table += self.DR

        return table
