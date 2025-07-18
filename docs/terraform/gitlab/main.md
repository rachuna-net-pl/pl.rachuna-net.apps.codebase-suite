## 🏗️ Terraform - IAC - GITLAB
Moduł do pracy z Terraform, oferujący:

```mermaid
---
config:
  theme: base
  layout: elk
  look: classic
---
%%{init: {"themeVariables": {"background": "#fff"}} }%%
flowchart LR
    A(["Start"]) --> n4["Przygotowanie pliku konfiguracyjnego"]
    B["Generowanie szablonów"] --> D["Importowanie do Terraform state"]
    D --> n1["Analizowanie logów,<br>korekta konfiguracji"]
    D --> n2(["Stop"])
    n1 --> D
    n4 --> B
    n4 --> n5["Ręczna konfiguracja repozytorium"]
    n5 --> D

    %% Przypisanie klas
    class A Pine
    class B,D Sky
    class n1,n5 Peach
    class n2 Aqua,Pine

    %% Definicje stylów
    classDef Aqua stroke-width:1px, stroke-dasharray:none, stroke:#46EDC8, fill:#DEFFF8, color:#378E7A
    classDef Pine stroke-width:1px, stroke-dasharray:none, stroke:#254336, fill:#27654A, color:#FFFFFF
    classDef Sky stroke-width:1px, stroke-dasharray:none, stroke:#374D7C, fill:#E2EBFF, color:#374D7C
    classDef Peach stroke-width:1px, stroke-dasharray:none, stroke:#FBB35A, fill:#FFEFDB, color:#8F632D
    
```

**Generowanie konfiguracji**
- [Automatyczne generowanie definicji Terraform dla grupy GitLab](/ddocs/terraform/gitlab/generate/main.md)
- [Automatyczne generowanie definicji Terraform dla projektu GitLab](/ddocs/terraform/gitlab/generate/main.md)
- [Automatyczne generowanie definicji Terraform dla grupy wraz z jego dziećmi GitLab](/ddocs/terraform/gitlab/generate/main.md)

**Import zasobów:**
- Import istniejących zasobów GitLab do stanu Terraform](/docs/terraform/gitlab/import/main.md)


--- 
## Ręczna konfiguracja

1. Ustawienie providera
2. Ustawienie data [opcjoalnie] (np. kiedy integrujesz się z vault)
3. Dodanie katalogu `images`
4. Dodanie katalogu plików z parametrami (`data/allowed_avatar_group_types.json`, `data/allowed_avatar_project_types.json`, `data/allowed_project_types.json`)


## Analiza wyników importu

> [!important] Założenia
> 1. Użycie terraform import bezpośrednio do gitlab State w projekcie
> 2. Próbka danych 741 resources (11 group, 62 repozytoria)
> 3. Najwolniejszym elementem procesu jest wykonywanie polecenia `terraform import` (741x użyto polecenia)
> 4. Najpierw importowane są grupy, później repozytoria, a na końcu wszystkie parametry


**Import grup**
```mermaid
---
config:
    xyChart:
        width: 1400
        height: 600
        showDataLabel: true
---
xychart-beta
    title "Import gitlab groups %"
    x-axis [4.6, 4.7, 4.9, 5.0, 5.1, 9.6, 32.3, 33.0, 34.1, 47.1, 47.2, 51.9, 100.0]
    y-axis "Time (seconds)" 0 --> 140
    line [0.0, 11.555639, 22.721878, 34.639242, 46.282138, 58.05492, 69.757065, 81.091021, 92.414706, 105.62931, 118.580053, 131.889031, 131.890342]
```


**Import projektów**
```mermaid
---
config:
    xyChart:
        width: 1400
        height: 600
        showDataLabel: true
---
xychart-beta
    title "Import gitlab projects %"
    x-axis [0, 5, 6, 7, 7, 10, 11, 12, 14, 16, 17, 20, 22, 24, 26, 28, 30, 34, 35, 36, 37, 38, 39, 40, 42, 43, 44, 45, 46, 48, 49, 49, 50, 50, 51, 52, 53, 55, 58, 60, 62, 63, 63, 63, 65, 65, 66, 67, 67, 68, 69, 71, 74, 76, 76, 78, 80, 82, 85, 87, 89, 91, 94, 95, 98, 100]
    y-axis "Time (seconds)" 0 --> 800
    line [0, 11, 22, 34, 45, 56, 69, 82, 94, 106, 120, 132, 144, 155, 169, 181, 194, 205, 216, 227, 239, 251, 262, 275, 288, 300, 312, 323, 337, 349, 362, 373, 387, 400, 415, 429, 441, 456, 470, 483, 496, 508, 521, 533, 546, 559, 571, 584, 596, 608, 621, 632, 645, 657, 672, 685, 699, 712, 725, 743, 755, 769, 780, 795, 795]
```

**Import ustawień grup i repozytoriów**
```mermaid
---
config:
    xyChart:
        width: 1400
        height: 600
        showDataLabel: true
---
xychart-beta
    title "Import gitlab group and projects configuration %"
    x-axis [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 90, 92, 94, 96, 98, 100]
    y-axis "Time (minutes)" 0 --> 130
    line [0, 2, 5, 7, 9, 12, 15, 17, 19, 22, 24, 25, 28, 31, 34, 37, 39, 42, 45, 47, 50, 52, 54, 57, 60, 61, 63, 66, 69, 72, 74, 75, 77, 80, 82, 84, 88, 91, 93, 96, 99, 102, 105, 108, 111, 113, 116, 119, 121, 124]
```