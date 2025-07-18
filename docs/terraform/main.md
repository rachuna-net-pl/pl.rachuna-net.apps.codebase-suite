## 🏗️ Terraform - IAC - GITLAB
Moduł do pracy z Terraform, oferujący:

```mermaid
---
config:
  theme: base
  layout: elk
  look: classic
---
flowchart LR
    A(["Start"]) --> n4["Przygotowanie pliku konfiguracyjnego"]
    B["Generowanie szablonów"] --> D["Importowanie do Terraform state"]
    D --> n1["Analizowanie logów i korekta konfiguracji"]
    D --> n2(["Stop"])
    n1 --> D
    n4 --> B
    n4 --> n5["Dokonfigurowanie ręczne repozytorium"]
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

---
## Generatory

1. [IAC-GITLAB](/docs/terraform/gitlab/gitlab   /main.md)

---
## Importery:

1. [IAC-GITLAB](/docs/terraform/gitlab/import/main.md)