# FM Radio receiver realizovaný na mikrokontroléru Raspberry Pico
## Cíl projektu
Cílem projektu je realizovat FM enkodéru, který bude na displeji zobrazovat vybranou frekvenci a její parametry. Výstup z enkodéru bude poté přehráván  


### Členové týmu
- **Jakub Dibelka** - finální dokumentace projektu, video 
- **Martin Doucha** - ladění a pomoc tvorby programu
- **Matěj Jurka** - tvorba programu, ladění 

### Základní funkce
* **Příjmání signálu:** Přijímá signál který enkóduje
* **Přehrávání zvuku:** Přehrávání příjmaného signálu ve sluchátcích / reproduktoru
* **Změna frekvence:** Výběr FM frekvence pomocí rotačního enkodéru
* **Ovládání stanice:** pomocí periferií ovládat hlasitost a výběr oblíbené stanice 
* **Zobrazení údajů:** Zobrazení vybrané frekvence, nastavená hlasitost, RSSI, vybrané informace RDS

### Obsah
* [Cíl projektu](#cíl-projektu)
* [Lab1: Proposal and architecture](#lab1-proposal-and-architecture)
* [Lab2: Device modules](#lab2-device-modules)


## Lab1: Proposal and architecture

Během této hodiny jsme si přibližně rozdělili úlohy, seznámily se s moduly a navrhnuly základní podobu stanice FM radia.

### Využité moduly
- Raspberry pi Pico
- FM receiver modul Si4703
- Rotační enkodér 
- Potenciometr B10K
- LCD displej Nokia 5110
- boční periferie (tlačítko/joystick)

### Blokové schéma
Návrh blokového schématu pro naší aplikaci


## Lab2: Device modules
### testování senzorů
Návrh zapojení součástek pro testování + program potřebný pro zprovoznění
