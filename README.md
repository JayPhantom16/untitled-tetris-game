# Untitled Tetris Game

## Kā palaist projektu:

### Priekšnosacījumi
Pārliecinieties, ka datorā ir instalēts **Python (3.11+)**.

##  Instalācija un vides iestatīšana (Tikai pirmajai reizei)

Ja instalējat projektu pirmo reizi, lūdzu, izpildiet šīs darbības terminālī (projekta saknes mapē):

1. Izveidot virtuālo vidi (venv):

   `python -m venv .venv`

2. Aktivizēt virtuālo vidi:

  `.venv\Scripts\Activate.ps1` 

 (Pēc aktivizācijas termināļa rindiņas sākumā parādīsies (venv)).

3. Instalēt nepieciešamās bibliotēka:
   `pip install flask pyjwt requests pygame`

1. Datora terminālī parejiet mapē (cd C:\projekts\spele\api). Palaidiet serveri ar komandu python main.py.
2. Otrajā terminālī palaidiet spēles klientu: (`cd C:\projekts\spele\api` ➡   `python main.py` ).
3. Ievadiet savu vārdu un spiediet Enter!

##  Kā spēlēt (Vadība):

    Bultiņa pa kreisi / pa labi: Pārvietot figūru pa kreisi vai pa labi.

    Bultiņa uz leju: Paātrināt figūras krišanu.

    Bultiņa uz augšu: Pagriezt figūru.

    P: Pauze (pauzes ekrānā iespējams turpināt spēli, atgriezties izvēlnē vai iziet).

    Zelta figūras: Nejauši parādās dzeltenas zelta figūras. Pēc fiksēšanas laukumā jums ir 10 sekundes, lai tās izmantotu rindas notīrīšanā un iegūtu papildu punktus, pirms tās zaudē savu statusu.


## API adrešu saraksts

| Adrese (Endpoint) | Metode | Saturs un Apraksts |
| :--- | :--- | :--- |
| `/` | GET | Galvenā lapa: attēlo TOP 10 līderu tabulu, kurā katrs spēlētājs parādās tikai 1 reizi ar savu labāko rezultātu (TOP 1 izcelts zelta krāsā). |
| `/rules` | GET | Spēles noteikumi: detalizēts apraksts par vadību, zelta figūru mehāniku (10 sekunžu taimeri), līmeņiem un klienta palaišanu. |
| `/register` | POST | API: Reģistrē jaunu spēlētāju datubāzē, izmantojot lietotājvārdu un šifrētu paroli (201 Created / 400 Bad Request). |
| `/login` | POST | API: Autentificē lietotāju, salīdzina paroles hešu un izsniedz piekļuves tokenu (JWT). |
| `/scores` | POST | API: Saglabā spēlētāja sasniegto punktu skaitu un līmeni SQLite datubāzē ar datu validāciju (201 Created). |
| `/api/scores` | GET | API: Atgriež 10 labākos rezultātus JSON formātā spēles klienta lokālajam līderu skatam. |
| `/players/{name}/stats` | GET | API: Atgriež konkrētā spēlētāja nospēlēto spēļu skaitu un labāko rezultātu (404, ja spēlētājs nav atrasts). |

## Funkcionalitāte

    5 Grūtības līmeņi: Spēle kļūst straujāka atkarībā no sasniegtajiem punktiem.

    Dublēšanās novēršana: Gan lokālajā failā (scores.json), gan servera datubāzē katrs spēlētājs parādās tikai 1 reizi ar savu augstāko rezultātu.

    Bezsaistes režīms: Ja serveris nav sasniedzams, spēle saglabā rezultātus lokālajā scores.json failā.
