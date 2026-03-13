param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$EnvPath = ''
)

$ErrorActionPreference = 'Stop'

function Parse-EnvFile {
    param([string]$Path)

    $map = @{}
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) {
            return
        }

        $idx = $line.IndexOf('=')
        if ($idx -lt 1) {
            return
        }

        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()

        if (
            ($value.Length -ge 2) -and
            (
                ($value.StartsWith("'") -and $value.EndsWith("'")) -or
                ($value.StartsWith('"') -and $value.EndsWith('"'))
            )
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        $map[$key] = $value
    }

    return $map
}

function Assert-Equals {
    param(
        [hashtable]$EnvMap,
        [string]$Key,
        [string]$Expected,
        [System.Collections.Generic.List[string]]$Errors
    )
    if (-not $EnvMap.ContainsKey($Key)) {
        $Errors.Add("Variavel ausente: $Key (esperado: $Expected)")
        return
    }
    if ($EnvMap[$Key].ToLowerInvariant() -ne $Expected.ToLowerInvariant()) {
        $Errors.Add("Valor invalido para $Key. Atual: '$($EnvMap[$Key])' | Esperado: '$Expected'")
    }
}

function Assert-PositiveInt {
    param(
        [hashtable]$EnvMap,
        [string]$Key,
        [System.Collections.Generic.List[string]]$Errors
    )
    if (-not $EnvMap.ContainsKey($Key)) {
        $Errors.Add("Variavel ausente: $Key (esperado inteiro > 0)")
        return
    }
    $value = 0
    if (-not [int]::TryParse($EnvMap[$Key], [ref]$value) -or $value -le 0) {
        $Errors.Add("Valor invalido para $Key. Atual: '$($EnvMap[$Key])' | Esperado: inteiro > 0")
    }
}

Push-Location $ProjectRoot
try {
    $resolvedEnvPath = $EnvPath
    if (-not $resolvedEnvPath) {
        $resolvedEnvPath = Join-Path $ProjectRoot 'config/.env'
    }

    if (-not (Test-Path $resolvedEnvPath)) {
        Write-Host "Arquivo nao encontrado: $resolvedEnvPath" -ForegroundColor Red
        exit 1
    }

    $envMap = Parse-EnvFile -Path $resolvedEnvPath
    $errors = [System.Collections.Generic.List[string]]::new()

    Assert-Equals -EnvMap $envMap -Key 'DEBUG' -Expected 'False' -Errors $errors
    Assert-Equals -EnvMap $envMap -Key 'USE_HTTPS' -Expected 'True' -Errors $errors
    Assert-Equals -EnvMap $envMap -Key 'SESSION_COOKIE_SECURE' -Expected 'True' -Errors $errors
    Assert-Equals -EnvMap $envMap -Key 'CSRF_COOKIE_SECURE' -Expected 'True' -Errors $errors
    Assert-Equals -EnvMap $envMap -Key 'SECURE_SSL_REDIRECT' -Expected 'True' -Errors $errors
    Assert-Equals -EnvMap $envMap -Key 'SECURE_HSTS_INCLUDE_SUBDOMAINS' -Expected 'True' -Errors $errors
    Assert-Equals -EnvMap $envMap -Key 'SECURE_HSTS_PRELOAD' -Expected 'True' -Errors $errors
    Assert-PositiveInt -EnvMap $envMap -Key 'SECURE_HSTS_SECONDS' -Errors $errors

    if ($errors.Count -gt 0) {
        Write-Host "Baseline de seguranca de producao NAO conforme no ${resolvedEnvPath}:" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
        Write-Host "`nAjuste o arquivo .env do ambiente alvo e execute novamente." -ForegroundColor Yellow
        exit 1
    }

    $pythonExe = Join-Path $ProjectRoot 'venv\Scripts\python.exe'
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = 'python'
    }

    Write-Host "Arquivo $resolvedEnvPath validado. Executando auditoria estrita..." -ForegroundColor Cyan
    & $pythonExe manage.py auditar_seguranca --strict
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host 'Baseline de seguranca de producao validada com sucesso.' -ForegroundColor Green
}
finally {
    Pop-Location
}

