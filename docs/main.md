## Główne funkcjonalności

Aplikacja składa się z dwóch głównych modułów:

```
codebase-suite 
├── gitlab
│   ├── group
│   │   ├── list-badges  # Lista badges zdefiniowana w grupie gitlab
│   │   ├── list-ci      # Lista procesów CI/CD dla projektów w grupie
│   │   ├── list-labels  # Lista labels zdefiniowanych w grupie gitlab
│   │   └── list-vars    # Lista zmiennych w zdefiniowana w grupie gitlab
│   └── project
│       └── info         # Sprawdzanie projektu na podstawie lokalnej ścieżki do pobranego repozytorium lub po wskazaniu `full_path`
└── terraform
    ├── generate         # Generowanie plików terraform
    │   └── group        # Generowanie plików terraform dla grupy gitlab na podstawie modułu gitlab-group
    │   ├── groups       # Generowanie plików terraform dla grupy gitlab i ich dzieci
    │   └── project      # Generowanie plików terraform dla projektu gitlab na podstawie modułu gitlab-project
    └── generate         # Importowanie zasobów do terraform state
        └── gitlab       # Importowanie resources do terraform state dla iac-gitlab
```

### Architektura aplikacji

Aplikacja wykorzystuje modularne podejście z następującą strukturą:

- **Adapters** - adaptery do różnych systemów (Git, Terraform)
- **Commands** - implementacja poleceń CLI (GitLab, Terraform)
- **Config** - zarządzanie konfiguracją aplikacji
- **Connectors** - łączniki do zewnętrznych systemów (GitLab API, GraphQL)
- **Core** - podstawowe komponenty (Context, Logger)
- **Generators** - generatory kodu Terraform

## Instalacja

### Wymagania
- Python 3.12 lub nowszy
- Poetry (do zarządzania zależnościami)

### Kroki instalacji
```bash
# Utworzenie środowiska wirtualnego
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# lub
venv\Scripts\activate     # Windows

# Instalacja Poetry
pip install poetry

# Instalacja zależności
poetry install

# Uruchomienie aplikacji
codebase-suite --help
```


## Konfiguracja

### Zmienne środowiskowe

Aplikacja korzysta z następujących zmiennych środowiskowych:

- **GITLAB_URL** - URL instancji GitLab (domyślnie: https://gitlab.com)
- **GITLAB_TOKEN** - token dostępu do GitLab API
- **TERRAFORM_VERSION** - wersja Terraform do użycia

### Pliki konfiguracyjne

Aplikacja może być skonfigurowana przez:
- Parametry wiersza poleceń
- Zmienne środowiskowe
  
.envrc
```
## Gitlab
export GITLAB_FQDN="https://gitlab.com/"
export CI_USERNAME="xyz"
export GITLAB_TOKEN="***"


## Terraform
export TF_MODULE_gitlab_group_source="git@gitlab.com:pl.rachuna-net/infrastructure/terraform/modules/gitlab-group.git?ref=v1.2.1"
export TF_MODULE_gitlab_project_source="git@gitlab.com:pl.rachuna-net/infrastructure/terraform/modules/gitlab-project.git?ref=v2.0.2"
export TF_STATE_NAME_iac_gitlab="production"
```

## Szablony z konfiguracją

### Dostępne szablony dla terraform (`tf` lub `tf.json`)

Aplikacja zawiera wbudowane szablony Terraform dla:

- **gitlab-group** - szablony dla grup GitLab
- **gitlab-project** - szablony dla projektów GitLab

Szablony znajdują się w katalogu `templates/terraform/modules/` i wykorzystują silnik Jinja2.

### Tworzenie własnych szablonów

Możesz tworzyć własne szablony w oparciu o istniejące wzorce:

```bash
# Struktura katalogu szablonów
templates/
└── terraform/
    └── modules/
        ├── gitlab-group/
        │   ├── module.tf.j2
        │   ├── variables.tf.j2
        │   └── outputs.tf.j2
        └── gitlab-project/
            ├── module.tf.j2
            ├── variables.tf.j2
            └── outputs.tf.j2
```

## Rozwiązywanie problemów

### Częste problemy

1. **Błąd autoryzacji GitLab**
   ```bash
   export GITLAB_TOKEN="your-access-token"
   ```

2. **Problemy z encoding**
   - Aplikacja automatycznie konfiguruje encoding UTF-8 dla stdin/stdout

3. **Błędy Terraform**
   - Sprawdź czy Terraform jest zainstalowany i dostępny w PATH
   - Użyj opcji `--dry` do testowania bez wykonywania zmian
