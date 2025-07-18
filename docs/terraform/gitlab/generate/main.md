# Pobieranie informacji o grupie GitLab

---
**Generowanie konfiguracji dla grupy gitlab**

```bash
codebase-suite terraform generate gitlab group --full-path pl.rachuna-net --repository-path /repo/pl.rachuna-net/infrastructure/terraform/gitlab 
```

```
Usage: codebase-suite terraform generate gitlab group [OPTIONS]

  Generowanie plików terraform dla grupy gitlab na podstawie modułu gitlab-group

  https://gitlab.com/pl.rachuna-net/infrastructure/terraform/modules/gitlab-group

Options:
  -p, --full-path TEXT        Set full path to group (eg. pl.rachuna-net/app)  [required]
  -r, --repository-path PATH  Set local path to repository with a IaC definitions  [required]
  -t, --template-path PATH    Set path to template file definition gitlab group
  -f, --force                 Wymuś nadpisanie istniejących plików
  --json                      Generuj konfiguracje w formacie json
  --help                      Show this message and exit.
```

![](group/demo.gif)

> [!warning]
>
> szablony muszą być w odpowiednio nazwane
> `module.tf.j2` lub `modules.tf.json.j2` - definicja modułu
> `*.j2` zostaną wygenerowane i zapisane w katalogu grupy


**Generowanie konfiguracji dla project gitlab**

```bash
codebase-suite terraform generate gitlab project --full-path pl.rachuna-net/docs --repository-path /repo/pl.rachuna-net/infrastructure/terraform/gitlab 
```

```
Usage: codebase-suite terraform generate gitlab project [OPTIONS]

  Generowanie plików terraform dla projektu gitlab na podstawie modułu gitlab-project

  https://gitlab.com/pl.rachuna-net/infrastructure/terraform/modules/gitlab-project

Options:
  -p, --full-path TEXT        Set full path to group (eg. pl.rachuna-net/app)  [required]
  -r, --repository-path PATH  Set local path to repository with a IaC definitions  [required]
  -t, --template-path PATH    Set path to template file definition gitlab group
  -f, --force                 Wymuś nadpisanie istniejących plików
  --json                      Generuj konfiguracje w formacie json
  --help                      Show this message and exit.
```

![](project/demo.gif)

> [!warning]
>
> szablony muszą być w odpowiednio nazwane
> `module.tf.j2` lub `modules.tf.json.j2` - definicja modułu
> `*.j2` zostaną wygenerowane i zapisane w katalogu grupy

**Generowanie konfiguracji dla project gitlab**

```bash
codebase-suite terraform generate gitlab groups --full-path pl.rachuna-net --repository-path /repo/pl.rachuna-net/infrastructure/terraform/gitlab 
```

```
Usage: codebase-suite terraform generate gitlab groups [OPTIONS]

  Generowanie plików terraform dla grupy gitlab i ich dzieci

Options:
  -p, --full-path TEXT        Set full path to group (eg. pl.rachuna-net/app)  [required]
  -r, --repository-path PATH  Set local path to repository with a IaC definitions  [required]
  -t, --template-path PATH    Set path to template file definition gitlab group
  -f, --force                 Wymuś nadpisanie istniejących plików
  --json                      Generuj konfiguracje w formacie json
  --help                      Show this message and exit.
```

![](groups/demo.gif)