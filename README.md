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

# Megoldás
*Utoljára frissítve: 2021.11.24. 22:20*
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

### Néhány szó a bizonyításokban használt adatstruktúrákról
#### __Indexelés__
A sorokat fentről lefele, az oszlopokat balról jobbra számozzuk 0-tól 8-ig. Az `(r, c)` koordinátában az első mező jelöli a sort, a második az oszlopot.

A `Sudoku` osztályban - amely a program központi osztálya - számos segédinformáció van elmentve. Az `allowed` változó például megmondja, hogy az `i`. sor `j`. elemébe milyen számok kerülhetnek, míg a `rowpos` változó megmondja, hogy az `i`. sorban a `j` szám mely mezőkre mehet még. Ezek struktúrálisan úgy vannak megoldva, hogy mind a 4 ilyen jellegű változó (`allowed`, `rowpos`, `colpos`, `secpos`) tömbök tömbje, amiben a sorokat, oszlopokat és a számokat is 0-tól 8-ig vesszük, azaz `colpos[4][6]` azt mondja meg, hogy a 4. indexű oszlopon belül (ez összesen a ötödik, azaz a tábla közepén lévő) a *7-es* szám hova mehet még. A tömbök tömbjének elemei `diclen` objektumok, amik körülbelül `dict`-ek. Ugyanolyan konvenciókkal kell őket is indexelni, mint az eddigieket. Amennyiben az egyik kulcshoz `None` tartozik, az jelzi, hogy még megengedett ezt/ide írni, egyébként pedig egy `Knowledge` vagy `Deduction` példány, ami mutatja, *miért* nem megengedett az adott opció.

#### __Bizonyítások követése__
Az eddig levont következtetéseket, és hogy mi miből következett (például: ide nem jöhet 3, mert itt, itt és itt 3 van) objektum-orientáltan mentjük el. A `Deduction`-ök jeleznek következtetéseket, míg a `Knwoledge`-ok alapvető információk: így például minden `Deduction` tárol egy `Knowledge`-ot, ami megmondja, milyen következtetést von le. A `Deduction` a levont következtetés köré szerveződik, így több lehetséges indoklást is tud tárolni, hogy *miért* igaz a benne tárolt eredmény: minden ilyen indoklást egy `Consequence` reprezentál. Ő tárolja, mely egyéb információkon (`Deduction`/`Knowledge`) alapul a következtetés, és milyen szabályt alkalmazunk, hogy megkapjuk az eredményt (ez egy szöveges azonosító), ám magát a végeredményt nem tárolja. A `Deduction`-ök és az `IsValue` típusú `Knowledge`-ok pedig alapvetően nem csak a heapen éldegélnek, hanem a fent említett négy tömb egyikében, a megfelelő helyen el vnanak tárolva.

Azt, hogy mikor tényleg beírunk valamit, mit és hogyan használunk, a `ProofStep` osztály dönti el és fejti vissza az `__init__` metódusa során. Ő ezek után szépen struktúrálva elmenti az adott számbeírással kapcsolatos fontosabb információkat. Arról, hogy milyen gráffal dolgozik az `__init__` folyamán található egy ábra a `README.md` végén.

Ezek az osztályok felelnek továbbá a bizonyítások szép kiírathatóságáért is.

### Implementált következtetési módszerek
- Egy mezőn csak 1 szám lehet, mert az összes többi szerepel a sorában, oszlopában, vagy a négyzetében
- Egy soron/oszlopon/négyzeten belül valamelyik számnak egy adott mezőre kell mennie, mert az összes többiről ki van tiltva
- Egy sorban/oszlopban/négyzetben van két mező, hogy mindkettőbe már csak ugyanaz a két szám kerülhet: kkor a területen máshova nem kerülhet ez a két szám
- Egy sorban/oszlopban/négyzetben van két szám, hogy mindkettő csak két adott mezőre mehet: ekkor ezekre a mezőkre más nem mehet
- Egy négyzetben egy adott szám csak egy sorba/oszlopba mehet már: ekkor a sor/oszlop többi mezőjére nem kerülhet ez a szám
- Egy sorban/oszlopban már csak egy adott négyzeten belülre mehet egy szám: ekkor a négyzeten belül máshova nem mehet ez a szám

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