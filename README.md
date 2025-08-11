# SolverUni
SolverUni is a powerful command-line academic management tool designed for university students. It helps you track your courses, grades, and defines complex grading schemes to calculate the required scores on future evaluations to meet your academic goals. The tool leverages symbolic mathematics and optimization algorithms to provide precise solutions for both linear and non-linear grading formulas.

## Features

- **Course Management**: Add, view, and manage all your courses, including details like credits, semester, and year.
- **Evaluation Tracking**: Add evaluations for each course, update their grades as you receive them, and set grade ranges (min/max).
- **Symbolic Formula Engine**: Define complex, multi-level grading formulas using a simple, human-readable syntax. The system uses `sympy` to parse and manage these formulas symbolically.
- **Grade Optimization**: Calculate the optimal grades needed on remaining evaluations to achieve a target final grade. The optimizer can handle:
    - **Linear Systems**: Uses `scipy.optimize.linprog` for efficient linear programming solutions.
    - **Non-Linear Systems**: Uses `scipy.optimize.minimize` to solve complex, non-linear grading schemes.
- **Constraint Definition**: Add custom constraints to the optimization problem (e.g., `{Exam 1} + {Exam 2} >= 80`).
- **Persistent Storage**: All course data, formulas, and grades are saved locally in a SQLite database.
- **Clear CLI Interface**: Information is presented in clean, formatted tables for easy readability.

## How It Works

SolverUni's core logic resides in the `Curso` class, which transforms user-defined formulas into a solvable mathematical problem.

1.  **Symbolic Representation**: When you add a formula like `{Final Grade} = {Exams} * 0.6 + {Labs} * 0.4`, the tool uses `sympy` to create a symbolic expression. It handles nested formulas, automatically substituting variables until the main formula (`NP`) is expressed in terms of base evaluations.

2.  **Linearity Detection**: The system analyzes the final symbolic formula to determine if it's linear. This allows it to choose the most efficient optimization algorithm. This behavior can be overridden in `config.json`.

3.  **Optimization**:
    - For **linear** formulas, the problem is framed as a linear program. The objective is to satisfy the target final grade and all other constraints while keeping the weighted contribution of each unknown grade as balanced as possible.
    - For **non-linear** formulas, a non-linear optimization is performed. The objective function aims to minimize the variance between the unknown grades, encouraging a solution where the required scores are realistic and close to each other, while satisfying the target grade constraint.

4.  **Database Management**: An SQLite database (`db/db.sqlite3`) stores all information, ensuring data persistence between sessions. The `db.py` module provides a clean API for all database interactions.

## Installation and Usage

### Prerequisites

Ensure you have Python 3 installed. You will also need to install the required packages.

```bash
pip install sympy scipy numpy
```

### Running the Application

1.  Clone the repository:
    ```bash
    git clone https://github.com/markoker/solveruni.git
    cd solveruni
    ```
2.  Run the main script:
    ```bash
    python main.py
    ```

### Example Workflow

1.  From the main menu, select **"Menú de Cursos"** -> **"Agregar un curso"**.
2.  Enter the details for your new course.
3.  Select the course from the menu to see its details.
4.  Choose **"Modificar evaluaciones"** to add all the graded components of the course (e.g., Exam 1, Lab 1, Quiz 1). You can create multiple evaluations at once using range syntax (e.g., `Quiz [:5]` to create Quiz 1 through Quiz 5).
5.  Go back and select **"Modificar formulas"**. The tool will prompt you to define the formula for the main grade `NP`. Use the names of the evaluations you just created.
    - **Example Formula**: `{Exams}*0.6 + {Quizzes}*0.4`
    - The tool will see that `Exams` and `Quizzes` are not base evaluations and will prompt you to define them.
    - **Example for `Exams`**: `({Exam 1} + {Exam 2}) / 2`
    - The tool supports handy shortcuts for ranges: `{Quiz [+1:5]} / 5` is equivalent to `({Quiz 1} + {Quiz 2} + {Quiz 3} + {Quiz 4} + {Quiz 5}) / 5`.
6.  (Optional) Add any other course-specific rules under **"Modificar restricciones"**.
7.  As you get your grades, update them in the **"Modificar evaluaciones"** menu.
8.  Select **"Optimizar notas"** to calculate the scores you need on the remaining evaluations to pass or achieve your target grade.

## Configuration

You can modify the `config.json` file to change the default behavior:

```json
{
  "nota": {
    "aprobar": 55,   // Default passing grade
    "minima": 0,     // Default minimum possible grade
    "maxima": 100,   // Default maximum possible grade
    "objetivo": 70   // Default target grade
  },
  "optimizacion": {
    "mode": "mismoPeso",    // "mismoPeso" or "mismaNota" for optimization objective
    "forzarNoLineal": false // Set to true to always use the non-linear solver
  }
}
```

- **`mode`**:
    - `mismoPeso`: The optimizer tries to make the weighted contribution of each grade similar.
    - `mismaNota`: The optimizer tries to make the raw scores of each grade similar.
- **`forzarNoLineal`**: If `true`, the non-linear solver (`scipy.optimize.minimize`) will be used even if the system is detected as linear.
