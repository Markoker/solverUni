import numpy as np

def color_datos(val, threshold, reverse=False):
    colores = [167, 173, 179, 185, 149, 113, 77]

    if reverse:
        colores = colores[::-1]

    for i in range(len(threshold) - 1, -1, -1):
        if val >= threshold[i]:
            c = round(i / (len(threshold) - 1) * (len(colores) - 1))
            return colores[c]
    return colores[-1]


def colorear(texto, color):
    return f"\033[38;5;{color}m{texto}\033[0m"


def print_bool(val):
    if val:
        col = 77
    else:
        col = 167
    return colorear("█", col)


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)2

        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print("\r")


def printEquation(matrixCoefs, Vars, vectorResults):
    v = []
    for i in range(len(Vars)):
        v.append(f"{str(Vars[i]):>6}")
    v = ", ".join(v)
    print(f"[{v}]")

    for i in range(len(matrixCoefs)):
        row = []
        print("[", end="")
        for j in range(len(matrixCoefs[i])):
            row.append(f"{f"{matrixCoefs[i][j]:.2f}":>6}")
        row = ", ".join(row)
        print(f"{row}] [{f"{vectorResults[i]:.2f}":>6}]")

def printHistogramSuccess(success, notas):
    # Merge the two np arrays into a single one
    data = np.vstack((success, notas)).T 

    # Sort the data by the second column
    data = data[data[:,1].argsort()]

    threshold = 5

    hist = np.zeros((20,3))

    for i in range(len(data)):
        if data[i][1] > threshold:
            threshold += 5

        if data[i][0] == 1:
             hist[int(threshold/5 - 1)][2] += 1
        else:
            hist[int(threshold/5 -1)][1] += 1

    hist = hist/len(data)

    m = np.max(hist[:,1] + hist[:,2])

    hist = hist * 1/m 

    hist = np.round(hist * 20)
    hist[:,0] = 20 - np.sum(hist, axis=1)

    for j in range(20):
        print(f"{f'{(20-j)/20 * m:.2f}':>8} - ", end="")
        for i in range(len(hist)):
            if hist[i][0] > 0:
                t = colorear("█", 235 if j % 2 == 0 else 237)
                print(t*5, end="")
                hist[i][0] -= 1
            elif hist[i][1] > 0:
                print(colorear("█", 1) + colorear("█"*4, 167), end="")
                hist[i][1] -= 1 
            else:
                print(colorear("█", 2) + colorear("█"*4, 77), end="")
                hist[i][2] -= 1 
        print("")

    print(" "*11, end="")
    for i in range(20):
        print(f"{i * 5:<5}", end="")

def printDailyTaskPercentage(data, height=5):
    colors = [167, 173, 179, 185, 149, 113, 77]
    headers = ["Hoy", "30 días", "90 días", "180 días", "365 días"]
    offset = 0
    
    for i in range(len(headers)):
        if offset + len(headers[i]) > 147:
            break
    for i in range(height):
        for j in range(i, len(data), height):
            index = int(data[j] * len(colors))
            index = min(index, len(colors) - 1)
            print(colorear("██", colors[index]), end="")         
        print()
