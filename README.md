### Feladat
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

### Megoldás
*Utoljára frissítve: 2021.10.12. 16:00*
Jelenleg a kód mindig 8 mezőből következtet egy adott mező értékére.
    - Kitalálja, hogy egy mezőn csak 1 szám lehet, mert az összes többi szerepel a sorában, oszlopában, vagy a négyzetében
    - Kitalálja, hogy egy soron/oszlopon/négyzeten belül valamelyik számnak egy adott mezőre kell mennie, mert az összes többiről ki van tiltva
Végiggondolható, hogy mindkét módszer mindig legfeljebb 8 mezőt használ valójában.
Másrészt a projekthez tartozik egy egyértelműség-ellenőrző DFS is, amellyel be tudjuk látni, hogy az előző programnak képtelennek kell lennie a feladat megoldására. Nem talátunk (még) sudokut, ami egyértelmű lenne, és az első program nem oldotta volna meg.
Készül(t) a projekthez még sudoku szerkesztő, és input-output segédfüggvények is.