A sudoku solver that uses humanlike reasoning patterns with additional features.

# Quickstart:
Prerequisites: python3, pip

Install the required packages with:
```
pip install -r requirements.txt
```

Then run with:
```
py sudoku.py
```
Type `help` for available options. Note that the last option (with an empty command) is just hitting enter, which attempts to solve the given sudoku puzzle. Prior to this options can be set with input such as `k-optimization=true`/`k-opt=true`, `ip-time-limit=10`/`ip-t=10`. Note that most of this is quite forgiving and has multiple abbreviation options.

Try hitting enter, entering `proof` and `stats`, and then `playback` to run through the proof step by step with illustrations of the board state with pencilmarks included.

`ban <cells> <values>` and `set <row> <column> <value>` can be used to make 'Deus-ex' steps if the solver cannot progress and you see that a given field cannot/has to contain a given number. Note that if 'Deus-ex' step is wrong the solver can only detect the puzzle is unsolvable in obvious cases such as there being no valid number for a field, or no valid field for a number in an area.

# Abridged Problem Statement
The original problem was to solve a sudoku such that in one step you are only able to view the values in k fields. More specifically do this by creating a list of subsets of fields and loop over these subsets, trying to write numbers into new fields based on only that subset.

Notice that this is a lot closer to the way people solve a sudoku than how it is more easily done using a dfs or an IP solver, even though pencilmarking numbers into fields is not allowed.

*Instead of doing this our group decided to write a sudoku solver that emulates a human solve as closely as possible, also giving a proof of unicity. The problem statement inspired the feature of k-optimization*

# Solution
Last updated: 2021.11.30. 00:01

## Features
Solves a sudoku using a humanlike approach using constructing a proof for the solutions unicity along the way. Because of this proof it is assumed that **the solution is unique**, however this assumption is not used in any of the reasoning steps and can be checked using the method `is_unique` which uses the standard dfs solving method.

The code can be run from console on a sudoku that can be provided through
- a link to a URL (of format `http://nine.websudoku.com/<something>`)
- our console based sudoku editor
with the code otherwise solving a default problem.

This starts an interactive solver, through which detailed information can be acquired (and saved) about the current solve. There are options to turn of interactivity and only 

The interactive solver can also fetch steps of the proof and the required information to make given deductions, statistics about the solve, export information into a text document and contains multiple options for displaying the solution and its steps.

Another feature is *k-optimization*, which tries to minimize the `k` of the problem statements within the constraints of such a solve. This is somewhat of an afterthought in this project, so it isn't particularly fast and does not give an optimal solution to the original problem. To make matters worse, it uses an IP solver, therefore it can be *extremely* slow.

## Outline of how the solver works
The solver consists of two larger nested cycles:

At the end of each iteration of the outer cycle a number (if possible) is written into a field. Before entering a number *all possible* deductions of the implemented types are made in the inner cycle. Note that these deduction can be alternate proofs to deductions made in this same iteration of the outer cycle, for instance it is possible to know that a field may not contain a 3 because of both rules 4 and 5. (which will be elaborated on later)

When no further deduction can be made, a deduction of the form *"this field must contain the number x"* is chosen and x is written in the specified field. If *k-optimization* is disabled, this is done at random, otherwise a close to optimal choice is made. At this point the program goes back to looking for deductions.

In practice this is somewhat more complicated: for faster run speeds the program has options `greedy` and `reset-always`, which skip parts of the above outlined algorithm. If `reset-always` is on, then whenever a deduction if found the code starts looking for a new deduction starting from the simplest type going to the most complex instead of continuing from where it left off. If `greedy` is activated, then whenever a deduction that fills a field is found that field is filled. With *k-optimization* activated this would be extremely counterproductive, so the deduction is only made if it only uses elementary deductions of type `Knowledge`. (This in the projects current form means that it is an instance of `IsValue`, and is one of the four most elementary deduction rules with `k<=8`).

### Data structures used in the proof
#### __Indexing__
Rows up to down and columns are numbered left to right from 0 to 8. `(r,c)` coordinates are row and column.

The `Sudoku` class, which is the main class of the program, contains a lot of auxiliary variables. `allowed` contains the numbers that can go in the element `j` of row `i`, with `rowpos` containing the numbers that could still go in the `j`-th field of row `i`. In the implementation all four of `allowed`, `rowpos`, `colpos`, `secpos` are arrays of arrays coitaining `diclen` objects, which are practically `dict`s. When the value to a key is `None` this value can still go in the given field, otherwise it is an instance of `Knowledge` or `Deduction`, that explains *why* this option is not feasible.

#### __Following Proofs__
Deductions are stored in memory in an object-oriented manner. `Deduction`s are deductions and instances of `Knowledge` are quantums of information: thus every `Deduction` contains a `Knowledge`, which stores the inference made. A `Deduction` is based around the end result of a single deduction and can therefore store multiple proofs for the given deduction. Each proof is stored in an instance of `Consequence`. This contains what information (`Deduction`/`Knowledge` instances) this deduction uses and the deduction rule used, but the end result is not stored here. `Deductions` and `IsValue` type `Knowledge` instances are usually stored in one of the four aforementioned arrays in their designated positions.

When a number is written in a field the already filled fields used, and the `Deduction`s through which they are used are handled by the `ProofStep` class and are processed in its ``__init__`` method. After this the class saves the important data points to do with the chain of deductions that lead to the filling of the field. An ASCI "image" of the type of graph `__init__` handles can be found at the end of this readme.

These classes are also responsible for the pretty printing of proofs.

### Implemented deduction methods
For sake of brevity area will be short for row/column/square in this section.
- A field can only contain a given number, since all others are already in its row, column or square
- A number has to be in a given field of an area as it cannot go in any other fields in this area
- If there are two fields in an area that can only contain the same two numbers, then these numbers cannot go anywhere else in this area
- The same as the previous but with 3 instead of two
- If there are two numbers that can only go in two fields within an area, then no other numbers can go in these fields
- The same as the previous but with 3 instead of two
- If a number can only go in one row/col within a square, then it has to be within this squar in the given row/col
- If a number can only go in a given square within a row/col, then it has to go in that row/col within the given square
- Three corners of a rectangle only have two options each: AB, AC and BC, then C cannot go in the fourth corner (ordering of corners is important, and a more general interpretation of a rectangle is also implemented, see example)
```
EXAMPLE: C cannot go in the fourth corner. (marked with C+)
============================
|| --  AB  --|| -- AC  -- ||
|| --  --  --|| -- --  --||
|| --  BC  --|| -- C+  -- ||
============================
A more general example:
============================
|| C+  AB  C+|| --  AC  --||
|| --  --  --|| --  --  --||
|| BC  --  --|| C+  C+  C+||
============================
```
- A given number only has two position candidates within two parallel rows/cols that form a rectangle, then that number cannot go elswhere in the perpendicular cols/rows
- The same as the previous but with 3 instead of two

## Descriptions of some of the main classes
#### `Sudoku` - `sudoku.py`
Represents a sudoku problem, and is the central class of this project. Contains auxiliary information to help with the solving process, statistics, and settings.

The interactive solver is also handled by this class. Needs to be initialized with a given sudoku problem.

#### `Knowledge` - `tracker.py`
Contains information about a given field that is computed at some point during the solving process. This is an abstract class extended by classes containing actual information: `MustBe`, `CantBe`, `IsValue`. These classes contain information of that states that a number can/cannot go within a given field, or that it has already been filled in there.

#### `Deduction` - `tracker.py`
Stores the result (`Knowledge`) of a given deduction along with all the proofs found for it in `Consequence` instances.

#### `Consequence` - `tracker.py`
Contains a proof for a given deduction in the form of what `Deduction`/`Knowledge` instances are used to come to the given conclusion without storing the conclusion. Is mostly handled within `tracker.py`.

#### `ProofStep` - `tracker.py`
Chooses a field to fill from the available options in its `__init__`. Can run with *k-optimization* or without. *k-optimization* is done with an IP solver, so it can slow the program down immensely. *k-optimization* is not guaranteed to find the optimal k, since some deductions are removed (at random) to avoid circular reasoning.

This class is also responsible for pretty printing of proofs.

### Other classes
#### `Myprint` - `boardio.py`
Wrapper for the print funtcion to make printing to files with it easier.

#### `ConsoleApp` - `consoleapp.py`
For defining funcitons, their signatures, variables and patterns to enable parsing of input for a console app.

#### `diclen` - `util.py`
Practically a `dict`, but with some added funcitonality: can quickly calculate number of `None` values, and what keys these belong to.

Used to "answer questions" of type *"where can this number go in this row?"* or *"what numbers are still feasible for this field?"*. `None` means that the given position/number is still feasible. Otherwise the stored value (of type `Knowledge` or `Deduction`) is a proof of why this is not feasible.

## Descriptions of files
#### `boardio.py`
Deals with reading, parsing and printing of sudoku problems/board states.
- fancy or detailed printing of boards
- parsing of sudoku problems in text format
- fetching sudoku problem from the internet
- console based sudoku editor using `Getch.py`

#### `Getch.py`
Defines a `getch` function that enables reading of single characters in a fashion similar to C. Sadly reads `Ctrl` from `Ctrl+C` as a single character, thus when using this for input keyboard interrupts are not possible.

#### `consoleapp.py`
Framework for parsing conole commands making it possible to give commands like `ban 1,4 2,5: 3, 9`, `set 1 3 2`, `help`, `print --small` or `proof --reference 4:5`

The `ConsoleApp` class within enables parsing of commands like these, and extraction of parameters in a standard format. Mainly based on regexes.
#### `consolestyle.py`
Elements of the enums within this enable formatting of output to console. Note that results vary depending on used terminal, with cmd being quite limited and that of vscode being quite advanced.

#### `main.py`
Contains sudoku problems for testing and demoing.

#### `deduction_rules.py`
Contains implementations of various deduction rules. The logic that drives the solving process can be found here, with a separate function for each deduction rule.

#### `util.py`
Contains utility functions and classes. These mainly deal with conversions between different types of coordinates.

#### `tracker.py`
Object oriented solution for handling and storage of proofs through the `Knowledge`, `Consequence`, `Deduction` and `ProofStep` classes and descendants of these. Most of it deals with administrative tasks, with a lot of this being pretty printing.

**k-optimization** is implemented here within `ProofStep`.

#### `graph.py`
Contains `print_graph`, which prints an ASCII representation of the parts of possible proofs of a `Deduction` showing dependency relations.

#### `sudoku.py`
The most important file in the project, this is the actual main file that should be executed.
Implements the `Sudoku` class that:
- contains the interactive solver
- contains the higher level functions that are used in the solving process, and uses all our other tools
- makes it possible to run from conole

## Illustration of graph
The `0`s mark inferences that lead to the field being filled. `O`s are `DEductions`, and left of them are `Consequences` that contain possible proofs. (these are denoted by the first letter of the deduction rule that spawned them) These are connected to the inferences that they use through brances going down. The `*`s at the bottom represent units of elementary information.
```
                                                                                    ┌─┬0                              
                                                                                    a a                               
                                                                                    │ │                               
 ┌─────────────┬───┬───┬─────┬───────────────────────────────────────────┬─┬─┬──────┘ │                               
 ┌─────────────────────┬─────────────────────────────────────────────────┬───┬─┬─┬─┬─┬┘                               
 │             │   │   │     │                                           │ │ │ │ │ │ │                                
 │             │   │   │     │                                        ┌─┬O┌─┬O │ │ │ │                                
 │             │   │   │     │                                        n n n│n  │ │ │ │                                
 │             │   │   │     │                                        │ │ │││  │ │ │ │                                
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────────────────────────────────────┘ │ │││  │ │ │ │                                
 ┌─────────┬─────┬─────┬───┬─────────────────┬─────────────┬─┬─┬─┬─┬─┬─┬┘ │││  │ │ │ │                                
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────────────────────────────────────────┘││  │ │ │ │                                
 ┌─────────┬─────┬─────┬───┬─────────────────┬─────────────┬─┬─┬─┬─┬─┬─┬────┘  │ │ │ │                                
 │         │   │ │ │   │ │ │ │               │             │ │ │ │ │ │ │   │   │ │ │ │                                
 │         │   │ │ │   │ │ │ │              ┌O             │┌O │┌O┌O │ │   │  ┌O┌O │ │                    ┌0        ┌0
 │         │   │ │ │   │ │ │ │              n              │n  │n n  │ │   │  n n  │ │                    r         s 
 │         │   │ │ │   │ │ │ │              │              ││  ││ │  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬┘              ││  ││ │  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬────────────────┘  ││ │  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬────────────────────┘ │  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬──────────────────────┘  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬──────────────────────────────────┘ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬────────────────────────────────────┘  │ │                    │         │ 
 ┌─────────┬─────┬─────┬─┬───┬─────────────────────────────────────────────────────────────────────────┬─┬┘         │ 
 │         │   │ │ │   │ │ │ ┌─────────────────────────────────────────────────────────────┬─────────────────┬─┬─┬─┬┘ 
 │         │   │ │ │   │ │ │ │ │ │ │ │ │ │ │               │   │     │ │   │       │ │     │           │ │   │ │ │ │  
 │         │   │ │ │   │ │ │ │ │ │ │ │ │┌O┌O              ┌O  ┌O    ┌O┌O   │      ┌O┌O     │          ┌O┌O   │┌O┌O┌O  
 │         │   │ │ │   │ │ │ │ │ │ │ │ │h h               n   n     n n    │      n n      │          h h    │n n n   
 │         │   │ │ │   │ │ │ │ │ │ │ │ ││ │               │   │     │ │    │      │ │      │          │ │    ││ │ │   
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬┘ │               │   │     │ │    │      │ │      │          │ │    ││ │ │   
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬──┘               │   │     │ │    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬┘   │     │ │    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────┘     │ │    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬──────────┘ │    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────────────┘    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────────────────────────┘ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬──────────────────────────┘      │          │ │    ││ │ │   
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬──────────────────────────────────────────────────────────────┘ │    ││ │ │   
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬────────────────────────────────────────────────────────────────┘    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────────────────────────────────────────────────────┘ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬──────────────────────────────────────────────────────┘ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────────────────────────────────────────────────────────┘   
 │         │ │ │ │ │   │ │ │ │ │ │ │ │ │       │ │ │ │ │ │                 │               │                 │        
 │      ┌0 │ │ │ │ │┌0 │ │ │ │ │┌O┌O┌O┌O       │┌O┌O┌O┌O │                 │               │    ┌0┌0┌0       │        
 │      s  │ │ │ │ │s  │ │ │ │ │n n n n        │n n n n  │                 │               │    a s s        │        
 │      │  │ │ │ │ ││  │ │ │ │ ││ │ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─┬─┬─┬┘  │ │ │ │ ││  │ │ │ │ ││ │ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 │ │ │ │   ┌─┬─┬─┬─┬┘  │ │ │ │ ││ │ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬──┘ │ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────┘ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬──────┘ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────┘        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬──────────────────┘ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────────────────┘ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬──────────────────────┘ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────────────────────┘  │                 │               │    │ │ │        │        
 ┌─┬─────────────┬─────────────────────────────┬─────────────────────────────────────────┬─┬─┬─┬┘ │ │        │        
 │ │ │ ┌───────────────┬───────┬─────────────────────────────────────────────────────────────┬────┘ │        │        
 │ ┌─────────────────────────┬───────────────────────────────────────────────────────────┬─┬─┬──────┘        │        
 │ │ │ │   │ │ │ │ │   │ │ │ │ │               │         │                 │             │ │ │ │             │        
 * * * *   * * * * *   * * * * *               *         *                 *             * * * *             *        
```
# Magyar
# Feladat
Sudokut könnyű megoldani, ha jó a memóriánk. De mi a helyzet ha nagyon feledékenyek vagyunk, mondjuk egyszerre csak k mező értékére emlékszünk?
Mely k-kra tudunk megoldani sudokut a következő stratégiával? Még a feladvány ismerete nélkül készítünk egy L listát, aminek minden eleme k darab pozíció a 9*9-es tábláról.
Ezután megkapjuk a feladványt. Végigmegyünk a L-en újra és újra és minden elemére az ott adott k pozíció alapján próbálunk új számokat beírni a sudokuba. 
Ha egyszer úgy érünk végig L-en, hogy nem tudtunk beírni új számot akkor veszítettünk. Ha kitöltődik a feladvány nyertünk. 

Megjegyzés: A fenti stratégia mesterkéltnek tűnhet, de a legtöbb ember így oldja meg a sudokut. Pl először végignéznek minden 3*3-as blokkot, majd minden sort, majd minden
 oszlopot. És ha sikerült közben valamit beírni akkor kezdik elölről. Persze, általában nem tartják szigorúan ugyanazt a sorrendet, de ez nem lényeges. 
 Az ügyesebbek bevetnek bonyolultabb mintázatokat is. Több mezővel, pl 3 sort együtt figyelnek. 

Itt találtok néhány sudoku feladványt, amit teszteléshez lehet használni: http://lipas.uwasa.fi/~timan/sudoku/

Követelmények:
- Írjatok egy sudoku megoldót, ami minél kisebb k-ra működik. 
- Az L listát nem kell feltétlen legenerálni, a lényeg, hogy egy lépésben csak legfeljebb k mezőt használjunk egy következő kitalálásához. 
- Írjatok egy "nehéz sudoku generálót", azaz egy programot ami olyan sudokukat készít, amiket csak nagy k értékekkre tudtok megoldani. 
- A program ne fusson tovább pár másodpercnél. 

*Ez egy nagyon szép feladatleírás, mint az látszik. A mi célunk, hogy ezt ne teljesítsük, hanem egy Sudokut emberi módon oldó programot írjunk.*

# Installálás

Előfeltételek: python 3, pip

A következő paranccsal installálhatod a csomagokat:

```
pip install -r requirements.txt
```

Majd ezután a következőképpen futtathatod a programot:

```
py sudoku.py
```

# Megoldás
*Utoljára frissítve: 2021.11.30. 00:01*
## Tartalom
- *Mit tud a program?*
   - *Mellékes funkciók*
- *A megoldó működése nagy vonalakban*
   - *Néhány szó a bizonyításokban használt adatstruktúrákról*
      - *Indexelés*
      - *Bizonyítások követése*
   - *Implementált következtetési módszerek*
- *Néhány főbb osztály leírása*
   - *Mellékes osztályok*
- *Fájlok leírásai*
- *Ábra*

## Mit tud a program?
A program célja, hogy megoldjon egy sudokut "emberi lépésekkel", azaz számon lehet tartani, hogy melyik mezőbe mi kerülhet még, de nem szabad például (mély) dfs-t futtatni egy-egy következtetéshez. Fontos, hogy a kód persze nem emberien gondolkodik feltétlen, de a kidobott következtetés olyan, amit akár ember is megtehetett volna (legfeljebb nehezen találta volna meg). Mivel sorban következtetéseket akarunk levonni, így persze implicit feltesszük, hogy az adott sudoku **megoldása egyértelmű** (hisz csak így lehet bizonyítást adni rá, hogy *annak* kell lennie). Ennek az egyértelműségnek az ellenőrzéséhez készült dfs-es egyértelműség-ellenőrző.

A kód (`sudoku.py`) konzolról futtatható. Ekkor lehetőség van 
- megadni egy (adott honlapra mutató) URL-t, ahonnan a program letölti a megoldandó sudokut, vagy
- konzolos sudoku-szerkesztőt megnyitni, ahol a felhasználó maga készíthet feladványt, vagy
- paraméterek megadása nélkül a beépített alapértelmezett feladványt oldani.

Ekkor alapvetően egy interaktív megoldó indul el, amiben számos részletes információ lekérdezhető és elmenthető a megoldási folyamatról. Konzolról futtatás esetében alternatívan lehetőség van az interaktivitás kikapcsolására, és egyszerűen a megoldás lekérdezésére ehelyett.

### Mellékes funkciók
A megoldón túl számos további érdekes résszel rendelkezik a program. Fent már említésre került, hogy van egyértelműség-ellenőrző. 

Emellett az interaktív megoldó igen komoly képességekkel bír: szépen, akár hivatkozásostúl ki tudja íratni a bizonyítás kívánt részletét, lehet statisztikákat lekérdezni belőle, szöveges dokumentumba exportálni minden fontosabb összegyűjtött információt, vagy éppen számos különböző kiíratási mód közül válogatni.

Egy további apró plusz a *"k-optimalizáció"*, azaz egy (igen-igen gyenge) extra lépés, aminek aktiválásával a program megpróbálja az eredeti feladatkitűzésben szereplő módon `k` értékét minimalizálni minden lépésben. Mivel ez közel sem volt igazi célunk, jelenleg ez lassú, buta, és mivel egy IP-megoldót használ, nem is feltétlen áll le időben.

## A megoldó működése nagy vonalakban
A megoldó két nagyobb egymásba ágyazott ciklusból áll. 

Minden ciklusban 1 számot szeretnénk a táblázatba beírni. Ehhez a beírás előtt addig próbálunk meg új, eddig ismeretlen következtetéseket levonni, amíg csak lehet. Ha valami olyat láttunk be, amit már ismerünk, de más módon, akkor ezt az alternatív utat is elmentjük: például tudhatjuk egy mezőről, hogy oda nem mehet 3 a lent részletezett 4. és 5. szabály alapján is.

Miután nem tudtunk új következtetést levonni, kiválasztunk 1 olyan következtetést, ami azt mondja, hogy *"ide ezt kell írni"*, és végrehajtjuk. Ha nincs *k-optimalizáció*, ezt bután tesszük meg, egyébként pedig kicsit gondolkodunk, hogy a lehető legjobbat válaszzuk. Miután megtörtént a beírás, elkezdünk újra ismeretlen következtetéseket keresni, és megy tovább a ciklus.

Ennél persze az egész kicsit bonyolultabb. A program gyorsítása kedvéért elérhető két beállítás (`greedy` és `reset-always`), amik egy-két részét kivágják a fenti kódnak. Ha a `reset-always` be van kapcsolva, akkor bármelyik olyan következtetés után, ami nem azt mondja, hogy valamit be kell írni, a következő következtetés keresését nem innen fogja folytatni a program, hanem visszaugrik a legegyszerűbb típusú következtetésekhez, és onnan indul elölről. Ha a `greedy` be van kapcsolva, akkor amikor talál egy olyan következtetést, ami egy mező kitöltését vonja maga után, akkor megszakítja a következtetés-keresést, és beírja a most talált számot. Persze ha be van kapcsolva a *k-optimalizáció*, akkor ez igen buta dolog lenne, így ebben az esetben a megszakításnak az plusz feltétele, hogy a következtetés csak "elemi" dolgokat használjon, azaz hogy minden, amire támaszkodik az `Knowledge` példány legyen (ez pedig jelenleg azt jelenti, hogy `IsValue` példány, továbbá a 4 legalapvetőbb szabály egyikéről van szó, és `k<=8` lesz).

### Néhány szó a bizonyításokban használt adatstruktúrákról
#### __Indexelés__
A sorokat fentről lefele, az oszlopokat balról jobbra számozzuk 0-tól 8-ig. Az `(r, c)` koordinátában az első mező jelöli a sort, a második az oszlopot.

A `Sudoku` osztályban - amely a program központi osztálya - számos segédinformáció van elmentve. Az `allowed` változó például megmondja, hogy az `i`. sor `j`. elemébe milyen számok kerülhetnek, míg a `rowpos` változó megmondja, hogy az `i`. sorban a `j` szám mely mezőkre mehet még. Ezek struktúrálisan úgy vannak megoldva, hogy mind a 4 ilyen jellegű változó (`allowed`, `rowpos`, `colpos`, `secpos`) tömbök tömbje, amiben a sorokat, oszlopokat és a számokat is 0-tól 8-ig vesszük, azaz `colpos[4][6]` azt mondja meg, hogy a 4. indexű oszlopon belül (ez összesen a ötödik, azaz a tábla közepén lévő) a *7-es* szám hova mehet még. A tömbök tömbjének elemei `diclen` objektumok, amik körülbelül `dict`-ek. Ugyanolyan konvenciókkal kell őket is indexelni, mint az eddigieket. Amennyiben az egyik kulcshoz `None` tartozik, az jelzi, hogy még megengedett ezt/ide írni, egyébként pedig egy `Knowledge` vagy `Deduction` példány, ami mutatja, *miért* nem megengedett az adott opció.

#### __Bizonyítások követése__
Az eddig levont következtetéseket, és hogy mi miből következett (például: ide nem jöhet 3, mert itt, itt és itt 3 van) objektum-orientáltan mentjük el. A `Deduction`-ök jeleznek következtetéseket, míg a `Knwoledge`-ok alapvető információk: így például minden `Deduction` tárol egy `Knowledge`-ot, ami megmondja, milyen következtetést von le. A `Deduction` a levont következtetés köré szerveződik, így több lehetséges indoklást is tud tárolni, hogy *miért* igaz a benne tárolt eredmény: minden ilyen indoklást egy `Consequence` reprezentál. Ő tárolja, mely egyéb információkon (`Deduction`/`Knowledge`) alapul a következtetés, és milyen szabályt alkalmazunk, hogy megkapjuk az eredményt (ez egy szöveges azonosító), ám magát a végeredményt nem tárolja. A `Deduction`-ök és az `IsValue` típusú `Knowledge`-ok pedig alapvetően nem csak a heapen éldegélnek, hanem a fent említett négy tömb egyikében, a megfelelő helyen el vannak tárolva.

Azt, hogy mikor tényleg beírunk valamit, mit és hogyan használunk, a `ProofStep` osztály dönti el és fejti vissza az `__init__` metódusa során. Ő ezek után szépen struktúrálva elmenti az adott számbeírással kapcsolatos fontosabb információkat. Arról, hogy milyen gráffal dolgozik az `__init__` folyamán található egy ábra a `README.md` végén.

Ezek az osztályok felelnek továbbá a bizonyítások szép kiírathatóságáért is.

### Implementált következtetési módszerek
- Egy mezőn csak 1 szám lehet, mert az összes többi szerepel a sorában, oszlopában, vagy a négyzetében
- Egy soron/oszlopon/négyzeten belül valamelyik számnak egy adott mezőre kell mennie, mert az összes többiről ki van tiltva
- Egy sorban/oszlopban/négyzetben van két mező, hogy mindkettőbe már csak ugyanaz a két szám kerülhet: akkor a területen máshova nem kerülhet ez a két szám
- Egy sorban/oszlopban/négyzetben van három mező, hogy mindháromba már csak ugyanaz a három szám kerülhet: akkor a területen máshova nem kerülhet ez a három szám
- Egy sorban/oszlopban/négyzetben van két szám, hogy mindkettő csak két adott mezőre mehet: ekkor ezekre a mezőkre más nem mehet
- Egy sorban/oszlopban/négyzetben van három szám, hogy mindhárom csak három adott mezőre mehet: ekkor ezekre a mezőkre más nem mehet
- Egy négyzetben egy adott szám csak egy sorba/oszlopba mehet már: ekkor a sor/oszlop többi mezőjére nem kerülhet ez a szám
- Egy sorban/oszlopban már csak egy adott négyzeten belülre mehet egy szám: ekkor a négyzeten belül máshova nem mehet ez a szám
- Egy téglalap három sarkába rendre csak az AC, AB, BC számok vannak: ekkor a téglalap negyedik sarkába nem kerülhet C. (Ez igaz 4 tagú körökre is, nem csak téglalapokra)
- Két sorban/oszlopban csak 2 helyre kerülhet egy szám és ez a négy mező téglalapot alkot: ekkor a téglalap oszlopaiban/soraiban máshova nem mehet ez a szám
- Három sorban/oszlopban legfeljebb 3 helyre kerülhet egy szám és ezek legfeljebb 3 oszlopot/sort határoznak meg összesen: ekkor ezekben a oszlopok/sorokban máshova nem mehet ez a szám

## Néhány főbb osztály leírása
#### `Sudoku` - `sudoku.py`
Egy sudoku feladványt reprezentáló osztály. Ez a projekt "csúcsosztálya". Számos mellékes segédinformációt elment, hogy segítse a megoldási folyamatot. Emellett tárol statisztikákat és beállításokat is.

Ő bonyolítja le az interaktív megoldót is, és belőle közvetlen hívható az egyértelműség-ellenőrző. Egyből egy kész feladvánnyal kell inicializálni.

#### `Knowledge` - `tracker.py`
Valamilyen információt tárol egy adott mezőről, ami a megoldás során derült ki. Ez egy absztrakt osztály, amiből a konkrét információt tároló osztályok származnak: `MustBe`, `CantBe`, `IsValue`. Ezek megmondják, hogy az adott mezőbe valamilyen számot muszáj/nem lehet írni, illetve már írva van.

#### `Deduction` - `tracker.py`
Egy adott következtetést tárol el, azaz van egy `Knowledge` benne, amire ő meg tudja mondani, miért igaz. Ezt úgy teszi, hogy az összes lehetséges indoklását (hiszen több úton is eljuthattunk ehhez az eredményhez!) egy-egy `Consequence` példányban elmenti.

#### `Consequence` - `tracker.py`
Eltárol egy indoklást, azaz hogy melyik korábbi információkat (`Deduction`/`Knowledge`) kell felhasználni, és azokra milyen szabályt kell alkalmazni, hogy a szükséges eredmény kijöjjön - ám az eredményt nem menti el. Cél, hogy ezt az osztályt ne kelljen igazán látni a `tracker.py`-on kívül.

#### `ProofStep` - `tracker.py`
Az `__init__`-jében sok lehetséges számbeírás közül választ egyet. Tud *k-optimalizálni* ebben, de nélküle is lefut. A *k-optimalizációt* IP megoldóval végzi, így sajnos lassú és nem megbízható az a rész. Gyakran még az IP megoldó sem tud a pontos eredményre jutni, mert elképzelhető, hogy a sok lehetséges indoklás közt van ciklikus is, amit a megoldónak átadás előtt megsemmisítünk óvatlan módon, nem figyelve, hogy ezzel ne rontsuk el a minimális `k` értéket.

Másrészt tud kiíratni bizonyítást szépen.

### Mellékes osztályok
#### `MyPrint` - `boardio.py`
Felülírja a beépített `print` függvényt, hogy 1 paranccsal át lehessen állítani, hova nyomtat, és ne kelljen minden `print` hívásban átállítani.

Azért készült, mert sokminden van, amit egyaránt akarunk konzolra és fájlba is nyomtatni, és nem akartunk mindent kétszer (`with open` és `print`) megírni.

#### `ConsoleApp` - `consoleapp.py`
Definiálni lehet vele függvényeket és azok szignatúráit, illetve változókat és a mintáikat, és ezek után képes könnyen parsolni ezen függvények/változók szöveges hívásait. Nem végzi el a függvényhívást, csak kinyeri belőle a fontos adatokat, és standard formába rendszerezve visszaadja.

#### `diclen` - `util.py`
Lényegében egy `dict`, csak gyorsan le lehet belőle kérdezni néhány gyakori információt, ami nekünk kell: hány `None` értéke van, mely kulcsokhoz tartozik `None`, milyen nem `None` értékei vannak.

Alapvetően olyan funkcióban használjuk, hogy egy `diclen` mindig egy olyan jellegű kérdésre ad választ, hogy *"ebben a sorban ez a szám hova mehet?"* vagy *"erre a mezőre milyen szám kerülhet még?"*. A `None` jelzi, hogy még az adott pozíció/szám megengedett, egyébként pedig a tárolt érték (egy `Knowledge` vagy `Deduction` példány) mondja meg, hogy *miért* nem megengedett ez.

## Fájlok leírásai
#### `boardio.py`
Sudoku feladványok (táblázatok) beolvasásával és kiíratásával foglalkozik.
- táblázatok fancy és/vagy részletes kiíratása
- szöveges formában reprezentált feladványok parse-olása
- feladvány internetről letöltése
- konzolos sudoku editor a `Getch.py` segítségével

#### `Getch.py`
Ad egy `getch` függvényt, amivel a C-hez hasonlóan be lehet olvasni egy (1) karaktert egyszerre (pythonban ez valamiért igen nehéz). Sajnos a `Ctrl+C`-ből a `Ctrl`-t is egy karakternek olvassa be, így mikor ez bekér, nem lehet interrputolni egyszerűen.

#### `consoleapp.py`
Alapvetően azt oldja meg, hogy az interaktív megoldónak tudjunk olyan parancsokat adni, hogy `ban 1,4 2,5: 3, 9`, `set 1 3 2`, `help`, `print --small` vagy `proof --reference 4:5`, ám ezt a funkcionalitást a konkrét feladattól függetlenül, általánosan oldja meg.

#### `consolestyle.py`
A benne található "enum"-ok elemeinek `print`-elésével színes/formázott szöveget lehet nyomtatni a konzolra. A ténylegesen működőképes formázások terminálonként eltérnek (Windows igen limitált, VSCode elég menő).
 
Ad tehát egy `ConsoleApp` osztályt, amivel könnyen lehet a fenti jellegű parancsokat parsolni, és kinyerni belőle a paramétereket valamilyen standard formátumban. Nagyrészt regexekre épül.

#### `main.py`
Néhány konkrét érdekes feladvány gyűjteménye.

#### `deduction_rules.py`
Különböző következtetési módszerek implementációinak gyűjteménye. A sudoku-oldás logikai része itt található. Minden következtetési módszernek saját függvénye van.

#### `util.py`
Segédfüggvényeket- és osztályokat tartalmaz. A segédfüggvények nagyrészt koordináta-konverziókal foglalkoznak.

#### `tracker.py`
Objektum-orientált megoldást nyújt a bizonyítások elmentésére és kezelésére a `Knowledge`, `Consequence`, `Deduction` és `ProofStep` osztályokon, illetve ezek néhány leszármazottján keresztül. Nagy része adminisztratív jellegű, a kód komoly része foglalkozik szép kiíratással. 

A **k-optimalizáció** is itt van implementálva, ahhoz egy relatíve nagy rész tartozik (`ProofStep` segédfüggvényei és `__init__`-je).

#### `graph.py`
Debug kiírató függvényt - `print_graph` - tartalmaz, ami egy szép reprezentációját adja egy adott lépésben a lehetséges bizonyítási lépések közül a relevánsaknak. Mutatja, hogyan függnek egymástól a különböző életben lévő `Knowledge`, `Consequence` és `Deduction` példányok.

#### `sudoku.py`
A legfontosabb fájl a projektben, **ez a futtatható állomány**. Ez implementálja a `Sudoku` osztályt. Három feladata van:
- az interaktív megoldó itt van implementálva
- a megoldással foglalkozó legmagasabb szintű függvények itt vannak leírva; ez a rész definiálja, mit is csinálunk a többi eszközünkkel pontosan
- a konzolról futtathatóságot ez a fájl biztosítja

## Ábra
Az ábrában a `0`-k jelölik az olyan következtetéseket, melyek beíráshoz vezetnek. Az `O`-k jelölik a `Deduction`-öket, majd tőlük balra-lent találhatók a `Consequence`-ek, amik a lehetséges indoklásokat tárolják (ezeket a hozzájuk tartozó szabály első betűje jelöli). Ők csatlakoznak azokhoz az információkhoz, amiket ők használnak, azaz lefele arra küldenek ágatak, amik nekik kellenek. Az ábra alján a `*`-ok jelölik az elemi információkat.
```
                                                                                    ┌─┬0                              
                                                                                    a a                               
                                                                                    │ │                               
 ┌─────────────┬───┬───┬─────┬───────────────────────────────────────────┬─┬─┬──────┘ │                               
 ┌─────────────────────┬─────────────────────────────────────────────────┬───┬─┬─┬─┬─┬┘                               
 │             │   │   │     │                                           │ │ │ │ │ │ │                                
 │             │   │   │     │                                        ┌─┬O┌─┬O │ │ │ │                                
 │             │   │   │     │                                        n n n│n  │ │ │ │                                
 │             │   │   │     │                                        │ │ │││  │ │ │ │                                
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────────────────────────────────────┘ │ │││  │ │ │ │                                
 ┌─────────┬─────┬─────┬───┬─────────────────┬─────────────┬─┬─┬─┬─┬─┬─┬┘ │││  │ │ │ │                                
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────────────────────────────────────────┘││  │ │ │ │                                
 ┌─────────┬─────┬─────┬───┬─────────────────┬─────────────┬─┬─┬─┬─┬─┬─┬────┘  │ │ │ │                                
 │         │   │ │ │   │ │ │ │               │             │ │ │ │ │ │ │   │   │ │ │ │                                
 │         │   │ │ │   │ │ │ │              ┌O             │┌O │┌O┌O │ │   │  ┌O┌O │ │                    ┌0        ┌0
 │         │   │ │ │   │ │ │ │              n              │n  │n n  │ │   │  n n  │ │                    r         s 
 │         │   │ │ │   │ │ │ │              │              ││  ││ │  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬┘              ││  ││ │  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬────────────────┘  ││ │  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬────────────────────┘ │  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬──────────────────────┘  │ │   │  │ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬──────────────────────────────────┘ │  │ │                    │         │ 
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬─┬─┬────────────────────────────────────┘  │ │                    │         │ 
 ┌─────────┬─────┬─────┬─┬───┬─────────────────────────────────────────────────────────────────────────┬─┬┘         │ 
 │         │   │ │ │   │ │ │ ┌─────────────────────────────────────────────────────────────┬─────────────────┬─┬─┬─┬┘ 
 │         │   │ │ │   │ │ │ │ │ │ │ │ │ │ │               │   │     │ │   │       │ │     │           │ │   │ │ │ │  
 │         │   │ │ │   │ │ │ │ │ │ │ │ │┌O┌O              ┌O  ┌O    ┌O┌O   │      ┌O┌O     │          ┌O┌O   │┌O┌O┌O  
 │         │   │ │ │   │ │ │ │ │ │ │ │ │h h               n   n     n n    │      n n      │          h h    │n n n   
 │         │   │ │ │   │ │ │ │ │ │ │ │ ││ │               │   │     │ │    │      │ │      │          │ │    ││ │ │   
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬┘ │               │   │     │ │    │      │ │      │          │ │    ││ │ │   
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬──┘               │   │     │ │    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬┘   │     │ │    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────┘     │ │    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬──────────┘ │    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────────────┘    │      │ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────────────────────────┘ │      │          │ │    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬──────────────────────────┘      │          │ │    ││ │ │   
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬──────────────────────────────────────────────────────────────┘ │    ││ │ │   
 ┌─────────────────────┬─┬───┬─┬─┬─┬─┬─┬────────────────────────────────────────────────────────────────┘    ││ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────────────────────────────────────────────────────┘ │ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬──────────────────────────────────────────────────────┘ │   
 │         ┌─┬─┬─┬─────────┬───────────────────┬─┬─┬─┬─┬─┬────────────────────────────────────────────────────────┘   
 │         │ │ │ │ │   │ │ │ │ │ │ │ │ │       │ │ │ │ │ │                 │               │                 │        
 │      ┌0 │ │ │ │ │┌0 │ │ │ │ │┌O┌O┌O┌O       │┌O┌O┌O┌O │                 │               │    ┌0┌0┌0       │        
 │      s  │ │ │ │ │s  │ │ │ │ │n n n n        │n n n n  │                 │               │    a s s        │        
 │      │  │ │ │ │ ││  │ │ │ │ ││ │ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─┬─┬─┬┘  │ │ │ │ ││  │ │ │ │ ││ │ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 │ │ │ │   ┌─┬─┬─┬─┬┘  │ │ │ │ ││ │ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬──┘ │ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────┘ │ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬──────┘ │        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────┘        ││ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬──────────────────┘ │ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────────────────┘ │ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬──────────────────────┘ │  │                 │               │    │ │ │        │        
 ┌─────────┬───┬─┬─┬───┬─┬─┬─┬────────────────────────┘  │                 │               │    │ │ │        │        
 ┌─┬─────────────┬─────────────────────────────┬─────────────────────────────────────────┬─┬─┬─┬┘ │ │        │        
 │ │ │ ┌───────────────┬───────┬─────────────────────────────────────────────────────────────┬────┘ │        │        
 │ ┌─────────────────────────┬───────────────────────────────────────────────────────────┬─┬─┬──────┘        │        
 │ │ │ │   │ │ │ │ │   │ │ │ │ │               │         │                 │             │ │ │ │             │        
 * * * *   * * * * *   * * * * *               *         *                 *             * * * *             *        
```
