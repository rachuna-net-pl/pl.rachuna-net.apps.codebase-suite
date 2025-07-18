# Import istniejących zasobów GitLab do stanu Terraform

```bash
codebase-suite terraform import gitlab --repository-path /repo/pl.rachuna-net/infrastructure/terraform/iac-gitlab -b
```

```
Usage: codebase-suite terraform import gitlab [OPTIONS]

  Importowanie resources do terraform state dla iac-gitlab (eg. https://gitlab.com/pl.rachuna-net/infrastructure/terraform/iac-gitlab)

Options:
  -r, --repository-path PATH  Set local path to repository with a IaC definitions  [required]
  --dry                       Uruchom w trybie dry-run
  --no-gitlab-state           Disable use gitlab terraform states
  -b, --progress              Enable progress bar
  --help                      Show this message and exit.
```

![](demo.gif)